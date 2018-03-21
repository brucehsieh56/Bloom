import os
import sys
import re
import numpy as np
import pandas as pd
import datetime
import urllib.request

from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import (QApplication, QWidget, QFileDialog, QLineEdit, 
	QInputDialog, QPushButton, QMessageBox, QVBoxLayout, QLabel)


class App(QWidget):


	def __init__(self):
		super().__init__()
		self.title = "Venus Flytrap"
		self.ZWSID = ""
		self.yr = datetime.datetime.now().year
		self.initUI()


	def initUI(self):
		
		# Widgets
		self.label = QLabel('Enter ZWSID:', self)
		self.text = QLineEdit(self) 
		btn = QPushButton("Load file", self)
		btn.clicked.connect(self.open_file)

		# Layout
		boxLayout = QVBoxLayout()
		boxLayout.addWidget(self.label)
		boxLayout.addWidget(self.text)
		boxLayout.addWidget(btn)
		self.setLayout(boxLayout)
		self.setWindowTitle(self.title)
		self.show()


	@pyqtSlot()
	def open_file(self):

		# get ZWSID
		self.ZWSID = self.text.text()


		def get_file(excel_file):
			""" func for reading the excel_file, querying the house price """

			# read excel file
			df = pd.ExcelFile(excel_file).parse(0)
			df = df.rename( 
				columns={
					"ShipStation Order Detail": "base_info", 
					"Unnamed: 1": "prds",
					"Unnamed: 3": "record",
					"Unnamed: 4": "date", 
					"Unnamed: 7": "unit_price", 
					"Unnamed: 9": "qty"
					}
				)

			# MAIN CODE:
			mask = df.prds.notnull().fillna(False)
			prds_list = df.prds[mask].values[::-1]
			pri_list = df.unit_price[mask].values[::-1]
			qty_list = df.qty[mask].values[::-1]

			# initialize
			prds, qty, unit_pri, total_pri = [], [], [], []
			temp_prds, temp_pri, temp_qty = [], [], []

			# extract info 1
			for i in range(prds_list.shape[0]):

			    if prds_list[i] != 'Item ID':
			        temp_prds.append(prds_list[i])
			        temp_pri.append(pri_list[i])
			        temp_qty.append(qty_list[i])
			             
			    else:
			        prds.append(temp_prds)
			        unit_pri.append(temp_pri)
			        qty.append(temp_qty)
			        total_pri.append((np.array(temp_pri)*np.array(temp_qty)).sum())
			        
			        temp_prds, temp_pri, temp_qty = [], [], []
		
			# reverse for simple cleaning
			prds, unit_pri, qty = prds[::-1], unit_pri[::-1], qty[::-1]
			total_pri = total_pri[::-1]

			# extract info 2
			mask = df.record.str.contains('Date Paid:').fillna(False).values

			# build df
			customer = pd.DataFrame({
				"name": df[mask].base_info.values, 
				"address1": df[np.roll(mask, 1)].base_info.str.replace(",", "").values, 
				"address2": df[np.roll(mask, 4)].base_info.str.replace(",", ""), 
				"date_paid": df[mask].date.values, 
				"amt_paid": df[np.roll(mask, 2)].date.values, 
				"record_no": df[np.roll(mask, 5)].date.values, 
				"product": ['+'.join(i) for i in prds], 
				"unit_price": ['+'.join(map(str, i)) for i in unit_pri],
				"qty": ['+'.join(map(str, i)) for i in qty],
				"total_price": [round(i, 2) for i in total_pri]
				})

			# extract info 3: zipcode
			customer['zipcode'] = customer.address2.str.extract('(\d{5})', expand=False)

			return customer


		def zillow(row, ZWSID):
			""" func for query house price given ZWSID """
    
		    # regular expression
			PATTERN = [
				'<code>.*</code>',
				'<zpid>.*</zpid>',
				'<city>.*</city>',
				'<state>.*</state>',
				'<latitude>.*</latitude>',
				'<longitude>.*</longitude>',
				'<amount currency="USD">.*</amount>',
				'<low currency="USD">.*</low>',
				'<high currency="USD">.*</high>',
				'<last-updated>.*</last-updated>'
				]

			# if no zipcode
			if row.isnull().zipcode:
				return pd.Series([np.nan for i in range(len(PATTERN))])

		    # query url
			url = 'http://www.zillow.com/webservice/GetSearchResults.htm?zws-id=' + \
				ZWSID + '&address=' + '+'.join(row.address1.split(" ")) + \
				'&citystatezip=' + row.zipcode

			# start query
			with urllib.request.urlopen(url) as response:

				html = response.read().decode(response.headers.get_content_charset())
				data = []
				for i in range(len(PATTERN)):
					
					# check error code
					if i == 0:

						obs = re.findall(PATTERN[i], html)
						obs = re.findall('>.*<', obs[0])[0][1:-1]

						# everything is fine
						if obs == '0':
							data.append(obs)

						# special case: ZWSID is invalid
						elif obs == '2':
							
							msg = QMessageBox.question(self, 
								'Error message', 
								"Invalid or missing ZWSID parameter", 
								QMessageBox.Close)
							
							break

						# special case: no house price info
						else:
							data = [obs]
							data.extend([np.nan for i in range(len(PATTERN)-1)])
							break
					else:

						# use the fisrt one (out of multiple results)
						if i == 1:
							html = html[:re.search('</result>', html).start()]
						
						obs = re.findall(PATTERN[i], html)
						obs = re.findall('>.*<', obs[0])[0][1:-1]
						data.append(obs)

			return pd.Series(data)


		def get_estimated_counts(first_name, sex=None, current_yr=self.yr, 
			min_age=10, max_age=90):

			# lowercase
			first_name = first_name.lower()
			sex = sex.lower()

			# create a mask
			mask = ((year_of_birth_df.year_of_birth <= (current_yr - min_age)) & 
				(year_of_birth_df.year_of_birth >= (current_yr - max_age)))
			mask &= (year_of_birth_df.sex == sex)
			mask &= (year_of_birth_df.first_name == first_name)

			# filter
			cur_df = year_of_birth_df[mask].drop('sex', axis=1)
			year_stats = (mortality_df[mortality_df.as_of_year == current_yr]
				[['year_of_birth', sex + '_prob_alive']])

			# interpolate
			cur_df['prob_alive'] = np.interp(cur_df.year_of_birth, 
				year_stats.year_of_birth, year_stats[sex + '_prob_alive'])

			# estimate alive ppl
			cur_df['estimated_count'] = cur_df['prob_alive'] * cur_df['count']

			return cur_df.set_index('year_of_birth')['estimated_count']


		def get_prob_male(first_name, current_yr=self.yr, min_age=10, max_age=90):
			""" predict probability of a ppl to be a male given first name """

			male_count = get_estimated_counts(first_name, 'm', current_yr, min_age, max_age).sum()
			female_count = get_estimated_counts(first_name, 'f', current_yr, min_age, max_age).sum()

			if male_count + female_count == 0:
				return 0.5

			return male_count * 1. / (male_count + female_count)


		def get_gender(first_name):
			""" return gender based on probability """

			if first_name.lower() in "ms.":
				return "F"

			probability = get_prob_male(first_name)
			if probability > .5:
				return "M"
			elif probability < .5:
				return "F"
			else:
				return ""



		# read files for gender prediction
		gov_data = ["mortality_table.csv.gz", "year_of_birth_counts.csv.gz"]
		if hasattr(sys, '_MEIPASS'):
			mortality_df = pd.read_csv(os.path.join(sys._MEIPASS, gov_data[0]))
			year_of_birth_df = pd.read_csv(os.path.join(sys._MEIPASS, gov_data[1]))
		else:
			mortality_df = pd.read_csv(os.path.join(os.path.abspath("."), gov_data[0]))
			year_of_birth_df = pd.read_csv(os.path.join(os.path.abspath("."), gov_data[1]))


		file_path, _ = QFileDialog.getOpenFileName(self, "", "", '*.xlsx')
		
		if file_path:

			customer = get_file(file_path)

			# customer = customer.iloc[:20,:]

			customer['p_gender'] = customer.apply(lambda row: get_gender(row['name'].split(" ")[0]), axis=1)

			# save file if no ZWSID provided
			if self.ZWSID == "":
		
				file_name, _ = QFileDialog.getSaveFileName(self,
					"Save your file",
					"customer_info_" + datetime.date.today().strftime("%Y%m%d"),
					'*.csv')
				
				if file_name:
					customer.to_csv(file_name, index=False)
					QMessageBox.about(self, "Nice", "Customer info extracted")

			else:

				# column names
				col = ['z_errorcode', 'zpid', 'z_city', 'z_state', 'z_lat', 
					'z_lon', 'z_price', 'z_lowprice', 
					'z_highprice', 'z_last_updated']

				customer = customer.iloc[:3,]	# debug

				# get house price
				temp = customer.apply(lambda row: zillow(row, self.ZWSID), axis=1)
				temp.columns = col

				# merge data
				df = pd.concat([customer, temp], axis=1)
				df = df[['z_lon', 'z_lat', 'address1', 'address2', 'amt_paid', 
					'date_paid', 'name', 'product', 'qty', 'record_no', 
					'total_price', 'unit_price', 'zipcode', 'z_errorcode', 
					'zpid', 'z_city', 'z_state', 'z_price', 'z_lowprice', 
					'z_highprice', 'z_last_updated']]

				# save file
				file_name, _ = QFileDialog.getSaveFileName(self,
					"Save your file",
					"customer_info_houseprice_" + datetime.date.today().strftime("%Y%m%d"),
					'*.csv')

				if file_name:
					customer.to_csv(file_name, index=False)
					QMessageBox.about(self, "Nice", "Customer info extracted")




if __name__ == '__main__':
	app = QApplication(sys.argv)
	ex = App()
	sys.exit(app.exec_())


