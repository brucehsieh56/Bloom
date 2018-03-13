// TODO: add different marker
// TODO: add hover info
// TODO: add Tooltips

// ===== Tooltips ==============================================================
$(function () {
  $('[data-toggle="tooltip"]').tooltip()
})

// ===== Slider ================================================================
var slider = document.getElementById("myRange");
var mkSize = document.getElementById("mkSize");
mkSize.innerHTML = slider.value;

slider.oninput = function() {

	// update marker size on bar
  mkSize.innerHTML = this.value;

  // update marker size on map
  let ly = layerPoints._layers;
  for (let i in ly) {

  	let j = ly[i]._layers;
  	j[Object.keys(j)[0]].setStyle({
  		radius: Number(this.value)
  	});
  }
}



// ===== Initialization ========================================================
var info = L.control();	// customer info
var geojson;

var	mapWiki = L.tileLayer("https://maps.wikimedia.org/osm-intl/{z}/{x}/{y}.png");
var mapOSM = L.tileLayer("http://{s}.tile.osm.org/{z}/{x}/{y}.png");
var	mapStaToner = L.tileLayer("http://a.tile.stamen.com/toner/{z}/{x}/{y}.png");
var	mapStaWater = L.tileLayer("http://c.tile.stamen.com/watercolor/{z}/{x}/{y}.jpg");
var baseMaps = { 
	"Wiki": mapWiki,
	"OSM": mapOSM,
  "StamenToner": mapStaToner, 
  "StamenWaterColor": mapStaWater
  };

// initialize a map
var geomap = L.map('geomap', {
  center: [37.0902, -98.35],
	zoom: 4,
	layers: [mapWiki]
	});

// for collecting data points
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
function get_geojson(x) {
	// func to convert input file into geojson 

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


// ===== Events ================================================================
document.getElementById('inputFile').onchange = function() {

	var file = this.files[0];	// get the input file
	var reader = new FileReader();	// initiate a file reader
	
	reader.onload = function() {

		let skipCount = 0;	// for reading column names
		let layerControl = L.control.layers(baseMaps).addTo(geomap);	// add control layer
		let columnNames = [];
		let obs = [];	// for collectin data (observations)
		let obsTable;	// for building table

		for (let x of this.result.split('\n')) {

			if (skipCount === 0) {	// get column names
				
				for (let j of x.split(",")) {
					columnNames.push({"title": j});
				}
				skipCount += 1;

			} else if (x == "") {	// avoid reading the empty line
					continue;
			
			} else {

				// save input file line by line
				obs.push(x.split(","));

				// build geojson object and add to the layer points
				geojson = L.geoJSON(get_geojson(x.split(",")), {
					pointToLayer: function (feature, latlng) {
						return L.circleMarker(latlng, geojsonMarkerOptions);
					},
					onEachFeature: onEachFeature
				})

				geojson.addTo(layerPoints);
				// L.geoJson(get_geojson(x.split(","))).addTo(layerPoints);

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
			scrollX: true
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
					// L.geoJson(get_geojson(x[i])).addTo(layerPoints);
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
				};

				// add back layer control
				layerControl = L.control.layers(baseMaps).addTo(geomap);
				console.log(geomap._layers);	// debug
    	};

	
	})}
	reader.readAsText(file);

};


