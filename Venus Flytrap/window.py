import os
import sys
import re
import numpy as np
import pandas as pd
import datetime
import urllib.request
from scipy.optimize import curve_fit
from PyQt5.QtCore import pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import (QApplication, QWidget, QFileDialog, QLineEdit, 
	QInputDialog, QPushButton, QMessageBox, QVBoxLayout, QLabel, QProgressBar)


class App(QWidget):
	# make a class App inherits from QWidget

	# valueChanged = pyqtSignal()
	# self.file.valueChanged.connect(self.print_id)
	# self.valueChanged.emit()

	def __init__(self):
		""" initizliation """

		# inherits from QWidget 
		super().__init__()

		# default values
		self.title = "Venus Flytrap"
		self.ZWSID = ""
		self.yr = datetime.datetime.now().year
		self.min_age = 10
		self.max_age = 90
		self.initUI()


	def initUI(self):
		
		layout = QVBoxLayout()

		# Widgets:
		# ZWSID txt
		label_ZWSID = QLabel("Enter ZWSID:", self)
		layout.addWidget(label_ZWSID)

		# txt input
		self.txt_ZWSID = QLineEdit(self)
		layout.addWidget(self.txt_ZWSID)

		# file input
		self.btn1 = QPushButton("Select an excel file", self)
		self.btn1.clicked.connect(self.load_file)
		layout.addWidget(self.btn1)

		# input file name
		self.file = QLabel("", self)
		layout.addWidget(self.file)

		# query button
		self.btn2 = QPushButton("Extract information", self)
		self.btn2.clicked.connect(self.extract_info)
		layout.addWidget(self.btn2)

		# progress bar
		self.progress = QProgressBar(self)
		layout.addWidget(self.progress)

		self.setLayout(layout)
		self.setWindowTitle(self.title)
		self.show()


	def load_file(self):
		""" func for getting file path """

		self.file_path, _ = QFileDialog.getOpenFileName(self, "", "", '*.xlsx')

		if self.file_path:
			self.file.setText(self.file_path)
			

	def update_progress(self):
		""" update progress bar """

		self.loading += self.p
		self.progress.setValue(self.loading)
		QApplication.processEvents()


	def extract_base_info(self):
		""" func for extract basic information """

		if self.file_path:

			df = pd.ExcelFile(self.file_path).parse(0)
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
			

	def extract_info(self):

		# initialize progress bar
		self.loading = 0

		# get ZWSID
		self.ZWSID = self.txt_ZWSID.text()

		# extract customer basic info
		customer = self.extract_base_info()

		# read data for gender prediction
		gov_data = ["mortality_table.csv.gz", "year_of_birth_counts.csv.gz"]
		if hasattr(sys, '_MEIPASS'):
			mot = pd.read_csv(os.path.join(sys._MEIPASS, gov_data[0]))
			yob = pd.read_csv(os.path.join(sys._MEIPASS, gov_data[1]))
		else:
			mot = pd.read_csv(os.path.join(os.path.abspath("."), gov_data[0]))
			yob = pd.read_csv(os.path.join(os.path.abspath("."), gov_data[1]))


		def get_estimated_counts(first_name, sex, cur_yr=self.yr, 
			min_age=self.min_age, max_age=self.max_age):

			# lowercase
			first_name = first_name.lower()
			sex = sex.lower()

			# create a mask
			mask = (
				(yob.year_of_birth <= (cur_yr - min_age)) & 
				(yob.year_of_birth >= (cur_yr - max_age)) & 
				(yob.sex == sex) & 
				(yob.first_name == first_name)
				)

			# filter
			cur_df = yob[mask].drop('sex', axis=1)
			year_stats = (mot[mot.as_of_year == cur_yr]
				[['year_of_birth', sex + '_prob_alive']])

			# interpolate
			cur_df['prob_alive'] = np.interp(cur_df.year_of_birth, 
				year_stats.year_of_birth, year_stats[sex + '_prob_alive'])

			# estimate alive ppl
			cur_df['estimated_count'] = cur_df['prob_alive'] * cur_df['count']

			return cur_df.set_index('year_of_birth')['estimated_count']


		def get_prob_male(first_name, cur_yr=self.yr, min_age=self.min_age,
			max_age=self.max_age):
			""" predict probability of a ppl to be a male given first name """

			# count
			male_count = get_estimated_counts(first_name, 'm').sum()
			female_count = get_estimated_counts(first_name, 'f').sum()

			# udpate progress
			self.update_progress()

			# calculate probability
			if male_count + female_count == 0:
				return 0.5
			else:
				return male_count * 1. / (male_count + female_count)


		def get_gender(row):
			""" return gender based on probability """

			# get first name
			first_name = row['name'].split(" ")[0].lower()

			# special case:
			if first_name in "ms.":
				return "F"

			# get gender according to the probability
			probability = get_prob_male(first_name)
			if probability > .5:
				return "M"
			elif probability < .5:
				return "F"
			else:
				return ""


		def gaussian(x, amp, mu, sigma):
			""" gaussian formula for curve fitting """
			return amp * np.exp(-(x-mu)**2/(2*(sigma**2)))


		def bimodal(x, a1, mu1, sigma1, a2, mu2, sigma2):
			""" two gaussian for curve fitting """
			return gaussian(x, a1, mu1, sigma1) + gaussian(x, a2, mu2, sigma2)


		def get_age(row, cur_yr=self.yr):
			""" guess age range"""

			# get parameters
			gender = row.p_gender
			first_name = row["name"].split(" ")[0]

			if gender == "M":
				count = get_estimated_counts(first_name, 'm')
			elif gender == "F":
				count = get_estimated_counts(first_name, 'f')
			else:
				return ""

			# beginning yr for age
			yr_base = count.index[0]

			# all yr
			yr_x = count.index.tolist()

			# try 1 guassian
			try:

				# boundary for (amp, mu, sigma)
				bounds = ((0, yr_base, 0), (count.max()*1.5, cur_yr, 15))

				# curve fitting
				popt, pcov = curve_fit(gaussian, yr_x, count, bounds=bounds)
				amp, mu, sigma = [int(abs(round(p))) for p in popt]

				# special case
				if mu + sigma >= cur_yr:
					# go to except
					raise Exception('Exception: 1 gaussian not work')

				# if sigma >= 10:
					# sigma = 10

				return str(cur_yr-mu) + "+-" + str(sigma)

			# try 2 gaussian
			except:

				# boundary for (amp1, mu1, sigma1, amp2, mu2, sigma2)
				bounds = ((0, yr_base, 0, 0, yr_base, 0), 
					(count.max()*1.5, cur_yr, 15, count.max()*1.5, cur_yr, 15))

				# expected (amp1, mu1, sigma1, amp2, mu2, sigma2)
				expected = (count.mean(), np.mean(yr_x)-1*np.std(yr_x), 10,
					count.mean(), np.mean(yr_x)+1*np.std(yr_x), 10)

				# curve fitting
				popt, pcov = curve_fit(bimodal, yr_x, count, expected, bounds=bounds)
				a1, mu1, sigma1, a2, mu2, sigma2 = [int(abs(round(p))) for p in popt]

				if a2 > a1:
					lower_bound = cur_yr - mu2 - sigma2
					if (lower_bound <= self.min_age) or (lower_bound < 0):
						return ""
					else:
						return str(cur_yr-mu2) + "+-" + str(sigma2)
				else:
					lower_bound = cur_yr - mu1 - sigma1
					if (lower_bound <= self.min_age) or (lower_bound < 0):
						return ""
					else:
						return str(cur_yr-mu1) + "+-" + str(sigma1)


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

						# if everything is fine
						if obs == '0':
							data.append(obs)

						# special case: invalid ZWSID
						elif obs == '2':
							
							msg = QMessageBox.question(self, "Error message", 
								"Invalid or missing ZWSID parameter", 
								QMessageBox.Close)
							
							break

						# special case: no house price info
						else:
							data = [obs]
							data.extend([np.nan for i in range(len(PATTERN)-1)])
							break
					else:

						# if mulitple results, use the fisrt one
						if i == 1:
							html = html[:re.search('</result>', html).start()]
						
						obs = re.findall(PATTERN[i], html)
						obs = re.findall('>.*<', obs[0])[0][1:-1]
						data.append(obs)

			return pd.Series(data)


		def get_house_price(customer, ZWSID=self.ZWSID):

			""" get house price given ZWSID """
			
			# get house price or not
			if self.ZWSID == "":

				file_name, _ = QFileDialog.getSaveFileName(self, 
					"Save your file",
					"customer_info_" + datetime.date.today().strftime("%Y%m%d"),
					'*.csv')

			else:

				# set column names
				col = ['z_errorcode', 'zpid', 'z_city', 'z_state', 'z_lat',
				'z_lon', 'z_price', 'z_lowprice', 'z_highprice', 'z_last_updated']

				# get house price
				temp = customer.apply(lambda row: zillow(row, self.ZWSID), axis=1)
				temp.columns = col

				# merge data
				customer = pd.concat([customer, temp], axis=1)
				customer = customer[['z_lon', 'z_lat', 'address1', 'address2', 
					'amt_paid', 'date_paid', 'name', 'product', 'qty', 
					'record_no', 'total_price', 'unit_price', 'zipcode', 
					'z_errorcode', 'zpid', 'z_city', 'z_state', 'z_price', 
					'z_lowprice', 'z_highprice', 'z_last_updated']]

				file_name, _ = QFileDialog.getSaveFileName(self, 
					"Save your file", 
					"customer_info_zillow_" + datetime.date.today().strftime("%Y%m%d"),
					'*.csv')

			# save file
			if file_name:
				customer.to_csv(file_name, index=False)
				QMessageBox.about(self, "Nice", "Customer info extracted")
		


		customer = customer.iloc[21:25]	# debug

		# setup progress bar increment unit
		self.p = 1 / len(customer) * 100

		# guess gender
		customer['p_gender'] = customer.apply(lambda row: get_gender(row), axis=1)

		# guess age
		customer['p_age'] = customer.apply(lambda row: get_age(row), axis=1)

		# get house price
		get_house_price(customer)



	

if __name__ == '__main__':
	app = QApplication(sys.argv)
	ex = App()
	sys.exit(app.exec_())