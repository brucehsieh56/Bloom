// TODO: add different marker
// TODO: add hover info
// TODO: add Tooltips
// TODO: add current # of points
// TODO: add weekly, monthly graph

// ===== Tooltips ==============================================================
$(function () {
  $('[data-toggle="tooltip"]').tooltip()
})

// ===== Slider ================================================================
var mkSize = document.getElementById("mkSize");

// initial marker size
mkSize.innerHTML = document.getElementById("myRange").value;

// update marker size on bar and map
document.getElementById("myRange").addEventListener("input", updateMarker);


// ===== Initialization ========================================================
var info = L.control();	// customer info on map
var geojson;	// saving data as geojson
var obs;
var mOSM = L.tileLayer("http://{s}.tile.osm.org/{z}/{x}/{y}.png");
var	mWiki = L.tileLayer("https://maps.wikimedia.org/osm-intl/{z}/{x}/{y}.png");
var	mToner = L.tileLayer("http://a.tile.stamen.com/toner/{z}/{x}/{y}.png");
var	mWater = L.tileLayer("http://c.tile.stamen.com/watercolor/{z}/{x}/{y}.jpg");
var baseMaps = { 
	"OSM": mOSM,
	"Wiki": mWiki,
  "StamenToner": mToner, 
  "StamenWaterColor": mWater
  };

// initialize a map
var geomap = L.map('geomap', {
  center: [37.0902, -98.35],
	zoom: 4,
	layers: [mOSM]
	});

// a layer for collecting data points
var layerPoints = L.layerGroup().addTo(geomap);

// set default marker style
var geojsonMarkerOptions = {
    radius: Number(mkSize.innerHTML),
    fillColor: "#33696d",
    color: "black",
    weight: 0.7,
    fillOpacity: 0.7
};


// ===== Functions =============================================================
function updateMarker() {

	// update marker size on bar
	mkSize.innerHTML = this.value;

	// update marker size on map
  let ly = layerPoints._layers;
  for (let i in ly) {

  	// layer of layer: no faster way?
		let j = ly[i]._layers;
		j[Object.keys(j)[0]].setStyle({
			radius: Number(this.value)
		});
  }
}


function get_geojson(x) {
	// convert input file into geojson 

	geoPoints = {
		"type": "Feature",
		"properties": {
			"product": x[7],
			"name": x[6],
			"amt_paid": x[4],
			"price": x[17]
		},
		"geometry": {
			"type": "Point",
			"coordinates": x.slice(0,2).map(parseFloat)
		}
	};

	return geoPoints;
}

info.onAdd = function(map) {
	this._div = L.DomUtil.create('div', 'info');	// create a div with class "info"
  this.update();
  return this._div;
};

info.update = function(props) {
  this._div.innerHTML = '<h4>Customer Info</h4>' +  (props ?
    '<b>' + props.name + '</b><br/>' + 
    'Amount paid: ' + props.amt_paid + 
    '<br/>House price: ' + props.price :
    'Hover over a point');
};

info.addTo(geomap);

function highlightFeature(e) {

  let layer = e.target;

  layer.setStyle({
    radius: Number(mkSize.innerHTML),
    fillColor: "#33696d",
    color: "black",
    weight: 1,
    fillOpacity: 1
  });

  if (!L.Browser.ie && !L.Browser.opera && !L.Browser.edge) {
  	layer.bringToFront();
  }
  
  info.update(layer.feature.properties);
}

function resetHighlight(e) {
  geojson.resetStyle(e.target);
  info.update();
}

function onEachFeature(feature, layer) {
  layer.on({
    mouseover: highlightFeature,
    mouseout: resetHighlight,
  });
}


let layerControl = L.control.layers(baseMaps).addTo(geomap);	// add control layer


// ===== Events ================================================================
document.getElementById('inputFile').onchange = function() {

	var file = this.files[0];	// get the input file
	var reader = new FileReader();	// initiate a file reader
	
	reader.onload = function() {

		let skipCount = 0;	// for reading column names
		let columnNames = [];
		obs = [];
		// let obs = [];	// for collectin data (observations)
		let obsTable;	// for building table

		for (let x of this.result.split('\n')) {

			if (skipCount === 0) {	

				// get column names
				for (let j of x.split(",")) {
					columnNames.push({"title": j});
				}
				skipCount += 1;

			} else if (x == "") {	// avoid reading the empty line
					continue;
			
			} else {

				// save input file line by line
				obs.push(x.split(","));

				// build geojson object and add to the layer points if having location
				if (x.split(",")[0] != "") {

					let row = x.split(",");
					 
					geojson = L.geoJSON(get_geojson(row), {
						pointToLayer: function (feature, latlng) {
							return L.circleMarker(latlng, geojsonMarkerOptions);
						},
						onEachFeature: onEachFeature
					})

					geojson.addTo(layerPoints);
					// L.geoJson(get_geojson(x.split(","))).addTo(layerPoints);
				}

			};

		};

		// MAIN CODE 2: TABLE
		// destory previous table content
		if ($.fn.dataTable.isDataTable('#obsTable')) {
			$('#obsTable').DataTable().destroy();
		};

		// build table	
		obsTable = $('#obsTable').DataTable( {
			data: obs,
			columns: columnNames,
			scrollX: true,
			scrollY: '60vh',
		});

		// MAIN CODE 3: Filter table content
		obsTable.on('search.dt', function() {

    	let numObs = obsTable.rows( { filter : 'applied'} ).nodes().length;
    	let x = obsTable.rows( { filter : 'applied'} ).data();

    	geomap.removeLayer(layerPoints);	// remove points
    	
    	if (numObs > 0) {

    		layerControl.remove(geomap);	// remove layer control
    		layerPoints = L.layerGroup().addTo(geomap);	// add back layer points

    		// add points to the layer
    		for (let i = 0; i < numObs; i++) {
					
    			// build geojson object and add to the layer if having location info
					if (x[i][0] != "") {
						geojson = L.geoJSON(get_geojson(x[i]), {
							pointToLayer: function (feature, latlng) {
								return L.circleMarker(latlng, geojsonMarkerOptions);
							},
							onEachFeature: onEachFeature
						})

						// update marker size
						geojson.setStyle({
							radius: Number(mkSize.innerHTML)
						});

						// add to layer
						geojson.addTo(layerPoints);
					}
				};

				// add back layer control
				layerControl = L.control.layers(baseMaps).addTo(geomap);
				console.log(geomap._layers);	// debug
    	};

	
	})}
	reader.readAsText(file);

};


// draw weekly chart
document.getElementById("btn").addEventListener("click", weeklyChart);

// ===== Chart Functions =======================================================
function weeklyChart() {
	// draw purchases by weekly

	let weekdayData = [];
	let dddd;	// d for data

	// DATA CLEANING
	// get date
	for (let i = 0; i < obs.length; i++) {
		weekdayData[i] = new Date(obs[i][5]);
		weekdayData[i] = weekdayData[i].toDateString().slice(0,3);	
	}

	// grouping by weekday
	dddd = d3.nest()
						.key( (d) => d)
						.rollup( (d) => d )
						.entries(weekdayData);

	// count the number of purchases weekly
	dddd.forEach( (d) => d.value = d.value.length);

	// sort by weekday
	let order = { "Mon": 1, "Tue": 2, "Wed": 3, "Thu": 4, 
								"Fri": 5, "Sat": 6, "Sun": 7};
	dddd.sort( (a, b) => order[a.key] - order[b.key]);

	// DRAWING
	// 1. remove old graph
	d3.select("#chart > svg").remove();

	// 2. default setting
	let margin = {top: 10, right: 10, bottom: 20, left: 20};
	let width = 500 - margin.left - margin.right;
	let height = 500 - margin.top - margin.bottom;
	let svg = d3.select("#chart")
							.append("svg")
								.classed("barchart", true)
								.attr("width", width + margin.left + margin.right)
								.attr("height", height + margin.top + margin.bottom)
							.append("g")
								.attr("transform", `translate(${margin.left}, ${margin.top})`);
	
	// 3. create scale
	let yScale = d3.scaleLinear()
									.domain([0, d3.max(dddd, (d) => Number(d.value))])
									.range([height, 0]);

	let xx = d3.scaleBand()
							.range([0, width])
							.padding(0.1)
	let xScale = xx.domain(dddd.map( (d) => d.key) );

	// 4. add axes								
	svg.append("g")
			.attr("class", "y axis")
  		.call(d3.axisLeft(yScale));
	
	svg.append("g")
			.attr("class", "x axis")
			.attr("transform", `translate(0, ${height})`)
			.call(d3.axisBottom(xScale));

	// 5. add bar chart
	svg.selectAll(".bar")
			.data(dddd).enter()
				.append("rect")
					.attr("x", (d) => xScale(d.key))
					.attr("width", xx.bandwidth())
					.attr("y", (d) => yScale(Number(d.value)))
					.attr("height", (d) => height - yScale(Number(d.value)));
}








