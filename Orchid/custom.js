// TODO: add different marker
// TODO: add hover info


var	mapWiki = L.tileLayer("https://maps.wikimedia.org/osm-intl/{z}/{x}/{y}.png");
var mapOSM = L.tileLayer("http://{s}.tile.osm.org/{z}/{x}/{y}.png");
var	mapStaToner = L.tileLayer("http://a.tile.stamen.com/toner/{z}/{x}/{y}.png");
var	mapStaWatercolor = L.tileLayer("http://c.tile.stamen.com/watercolor/{z}/{x}/{y}.jpg");
var baseMaps = { 
	"Wiki": mapWiki,
	"OSM": mapOSM,
  "StamenToner": mapStaToner, 
  "StamenWaterColor": mapStaWatercolor
  };


// initialize a map
var geomap = L.map('geomap', {
  center: [37.0902, -98.35],
	zoom: 4,
	layers: [mapWiki]
	});


// ===== Functions =============================================================
function get_geojson(x) {
	// func to convert input file into geojson 

	geoPoints = {
		"type": "Feature",
		"properties": {
			"product": x[7],
		},
		"geometry": {
			"type": "Point",
			"coordinates": x.slice(0,2).map(parseFloat)
		}
	};

	return geoPoints;
}


// ===== Events ================================================================
document.getElementById('inputFile').onchange = function() {

	var file = this.files[0];	// get the input file
	var reader = new FileReader();	// initiate a file reader
	
	reader.onload = function() {

		let skipCount = 0;	// for reading column names
		let layerPoints = L.layerGroup().addTo(geomap);	// for collecting data points
		let layerControl = L.control.layers(baseMaps).addTo(geomap);	// add control layer
		let columnNames = [];
		let obs = [];
		let obsTable;

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
				L.geoJson(get_geojson(x.split(","))).addTo(layerPoints);

			};
		};

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

		// filter table content
		obsTable.on('search.dt', function() {

    	let numObs = obsTable.rows( { filter : 'applied'} ).nodes().length;
    	let x = obsTable.rows( { filter : 'applied'} ).data();

    	geomap.removeLayer(layerPoints);	// remove points
    	
    	if (numObs > 0) {

    		layerControl.remove(geomap);	// remove layer control
    		layerPoints = L.layerGroup().addTo(geomap);	// add back layer points

    		// add points to the layer
    		for (let i = 0; i < numObs; i++) {
					L.geoJson(get_geojson(x[i])).addTo(layerPoints);
				};

				// add back layer control
				layerControl = L.control.layers(baseMaps).addTo(geomap);
				console.log(geomap._layers);	// debug
    	};

	
	})}
	reader.readAsText(file);

};


