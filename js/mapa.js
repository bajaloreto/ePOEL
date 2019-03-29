

mapboxgl.accessToken = 'pk.eyJ1IjoiaGVsZGVuOSIsImEiOiJjam54Z2sxankweDEyM3ZuZGd1OGV2b2NsIn0.xuzmd6tEA2f6lgJYLfW_VQ';
// This adds the map to your page
var map = new mapboxgl.Map({
// container id specified in the HTML
container: 'map',
// style URL
style: 'mapbox://styles/helden9/cjtkd5bsp2ura1fo2g5hrwfkw',
// initial position in [lon, lat] format
center: [ -111.348502,26.011936],
// initial zoom
zoom: 10,
bearing: -100
});
var hoveredStateId =  null;

map.on('load', function(e) {

  map.addSource("aprovechamiento_sustentable", {
  "type": "vector",
  "url": "mapbox://helden9.cjtronjo20l8ae5o4agw8et3k-8trxr"
  });

  map.addLayer({
    "id": "aprovechamiento-sustentable",
    "type": "fill",
    "source": "aprovechamiento_sustentable",
    "source-layer": "aprovechamiento_sustentable_poel",
    "layout":{
      "visibility":"none"
    },
    "paint": {
      "fill-color": "#d4edda",
      "fill-opacity": ["case",
      ["boolean", ["feature-state", "click"], false],
      1,
      0.5
      ]
  }
});

  map.addLayer({
    "id":"aprovechamiento_sustentable_lineas",
    "type":"line",
    "source": "aprovechamiento_sustentable",
    "source-layer": "aprovechamiento_sustentable_poel",
    "layout":{
      "visibility":"none"
    },
    "paint":{
      "line-color":"#155724"
    }
  });

  map.addSource("preservacion", {
  "type": "vector",
  "url": "mapbox://helden9.cjtropb4h02rh2xmutx2w0rtw-6jw2b"
  });

  map.addLayer({
    "id": "preservacion",
    "type": "fill",
    "source": "preservacion",
    "source-layer": "preservacion_poel_2014",
    "layout":{
      "visibility":"none"
    },
    "paint": {
      "fill-color": "#fff3cd",
      "fill-opacity": ["case",
      ["boolean", ["feature-state", "click"], false],
      1,
      0.5
      ]
  }
  });

  map.addLayer({
    "id":"preservacion_lineas",
    "type":"line",
    "source": "preservacion",
    "source-layer": "preservacion_poel_2014",
    "layout":{
      "visibility":"none"
    },
    "paint":{
      "line-color":"#856404"
    }
  });

  map.addSource("conservacion", {
  "type": "vector",
  "url": "mapbox://helden9.cjtrooin40lb0efn3kr4ad4o3-064rk"
  });

  map.addLayer({
    "id": "conservacion",
    "type": "fill",
    "source": "conservacion",
    "source-layer": "conservacion_poel_2014",
    "layout":{
      "visibility":"none"
    },
    "paint": {
      "fill-color": "#d1ecf1",
      "fill-opacity": ["case",
      ["boolean", ["feature-state", "click"], false],
      1,
      0.5
      ]
  }
  });

  map.addLayer({
    "id":"conservacion_lineas",
    "type":"line",
    "source": "conservacion",
    "source-layer": "conservacion_poel_2014",
    "layout":{
      "visibility":"none"
    },
    "paint":{
      "line-color":"#0c5460"
    }
  });

  map.addSource("restauracion", {
  "type": "vector",
  "url": "mapbox://helden9.cjtropxcj0l6k26qq3tsi9k6t-4jyxa"
  });

  map.addLayer({
    "id": "restauracion",
    "type": "fill",
    "source": "restauracion",
    "source-layer": "restauracion_poel_2014",
    "layout":{
      "visibility":"none"
    },
    "paint": {
      "fill-color": "#f8d7da",
      "fill-opacity": ["case",
      ["boolean", ["feature-state", "click"], false],
      1,
      0.5
      ]
  }
  });

  map.addLayer({
    "id":"restauracion_lineas",
    "type":"line",
    "source": "restauracion",
    "source-layer": "restauracion_poel_2014",
    "layout":{
      "visibility":"none"
    },
    "paint":{
      "line-color":"#721c24"
    }
  });


});
/*
map.on("click", "aprovechamiento-sustentable", function(e) {
if (e.features.length > 0) {
  hoveredStateId = e.features[0].id;
  alert(hoveredStateId);
if (hoveredStateId) {
map.setFeatureState({source: 'aprovechamiento_sustentable',sourceLayer:'aprovechamiento-sustentable', id: hoveredStateId}, { click: true});
}

//map.setFeatureState({source: 'aprovechamiento_sustentable',sourceLayer:'aprovechamiento_sustentable',id: hoveredStateId}, { click: true});
}
});

map.on("mouseleave", "aprovechamiento-sustentable", function() {
if (hoveredStateId) {
map.setFeatureState({source: 'aprovechamiento_sustentable',sourceLayer:'aprovechamiento-sustentable', id: hoveredStateId}, { click: false});
}
hoveredStateId =  null;
});
*/

map.on('click', function (e) {
    var features = map.queryRenderedFeatures(e.point, {
 layers: ['aprovechamiento-sustentable','preservacion', 'conservacion','restauracion']
 });
  if (!features.length) {
 return;
 }

  //  var markerHeight = -25, markerRadius = 25, linearOffset = 100;

var link =features[0].properties.nombre.substring(4);
document.getElementById("datos").innerHTML ='<h3>'+features[0].properties.nombre+' </h3> <ul class="list-group"> <li class="list-group-item"> Localidad de Referencia: '+features[0].properties.localidad_referencia+'</li>  <ul class="list-group"> <li class="list-group-item"> Superficie Total: '+features[0].properties.superficie_total+' Ha </li> <ul class="list-group"> <li class="list-group-item"> Poblacion: '+features[0].properties.poblacion+'</li> <li class="list-group-item"> Actividad: '+features[0].properties.actividad+'</li><li class="list-group-item"> Politica Ambiental: '+features[0].properties.politica_ambiental+'</li> <li class="list-group-item"> Fragilidad: '+features[0].properties.fragilidad+'</li> <li class="list-group-item"> Vulnerabilidad: '+features[0].properties.vulnerabilidad+'</li> <li class="list-group-item"> Presion: '+features[0].properties.presion+'</li> <li class="list-group-item"> Conflictos Potenciales: '+features[0].properties.conflictos_potenciales+'</li> <li class="list-group-item"> Ficha Completa: <a href="assets/pdf/3 Unidades de Gestion Ambiental/'+link+'.pdf" target="_blank"> PDF </a> </ul>';
$("#ugas-politica").css("display","none");
$("#datos").css("display","initial");
});

map.on('mousemove',function (e) {
    var features = map.queryRenderedFeatures(e.point, {
 layers: ['aprovechamiento-sustentable','preservacion', 'conservacion','restauracion']
 });


    if (features.length > 0) {
 //use the following code to change the
 //cursor to a pointer ('pointer') instead of the default ('')
 map.getCanvas().style.cursor = (features[0].properties.Name !== null) ? 'pointer' : '';
 }
 //if there are no points under our mouse,
 //then change the cursor back to the default
 else {
 map.getCanvas().style.cursor = '';
 }


});

var link = $('.checkbox');
for (var i = 0; i < link.length; i++) {


link[i].onclick = function (e) {
var clickedLayer = this.id;


var visibility = map.getLayoutProperty(clickedLayer, 'visibility');

if (visibility === 'visible') {
map.setLayoutProperty(clickedLayer, 'visibility', 'none');


} else {

map.setLayoutProperty(clickedLayer, 'visibility', 'visible');

}
};
}





function buildLocationList(data) {

var listing = document.getElementById('tabla_ugas');
while (listing.lastChild) {
listing.removeChild(listing.lastChild);
}
// Iterate through the list of stores
  for (i = 0; i < data.features.length; i++) {
    var currentFeature = data.features[i];
    // Shorten data.feature.properties to just `prop` so we're not
    // writing this long form over and over again.
    var prop = currentFeature.properties;
    // Select the listing container in the HTML and append a div
    // with the class 'item' for each store




 listing = document.getElementById('tabla_ugas');
     listing = listing.appendChild(document.createElement('tr'));

    listing.className = 'item';
    listing.id = 'listing-' + i;

    // Create a new link with the class 'title' for each store
    // and fill it with the store address

  listing.dataPosition = i;


    // Create a new div with the class 'details' for each store
    // and fill it with the city and phone number





      listing.addEventListener('click', function(e) {
        // Update the currentFeature to the store associated with the clicked link
        var clickedListing = data.features[this.dataPosition];

      // 1. Fly to the point associated with the clicked link
      flyToStore(clickedListing);
      // 2. Close all other popups and display popup for clicked store

      // 3. Highlight listing in sidebar (and remove highlight for all other listings)
      var activeItem = document.getElementsByClassName('active');
      if (activeItem[0]) {
        activeItem[0].classList.remove('active');
      }
      this.parentNode.classList.add('active');
      var link =clickedListing.properties.nombre.substring(4);

      document.getElementById("datos").innerHTML = '<h3>'+clickedListing.properties.nombre+' </h3> <ul class="list-group"> <li class="list-group-item"> Localidad de Referencia: '+clickedListing.properties.localidad_referencia+'</li>  <ul class="list-group"> <li class="list-group-item"> Superficie Total: '+clickedListing.properties.superficie_total+' Ha </li> <ul class="list-group"> <li class="list-group-item"> Poblacion: '+clickedListing.properties.poblacion+'</li> <li class="list-group-item"> Actividad: '+clickedListing.properties.actividad+'</li><li class="list-group-item"> Politica Ambiental: '+clickedListing.properties.politica_ambiental+'</li> <li class="list-group-item"> Fragilidad: '+clickedListing.properties.fragilidad+'</li> <li class="list-group-item"> Vulnerabilidad: '+clickedListing.properties.vulnerabilidad+'</li> <li class="list-group-item"> Presion: '+clickedListing.properties.presion+'</li> <li class="list-group-item"> Conflictos Potenciales: '+clickedListing.properties.conflictos_potenciales+'</li> <li class="list-group-item"> Ficha Completa: <a href="assets/pdf/3 Unidades de Gestion Ambiental/'+link+'.pdf" target="_blank"> PDF </a> </ul>';
      $("#datos").css("display","initial");
    });
    var link = listing.appendChild(document.createElement('td'));
    link.href = '#';
    link.className = 'title';

    link.innerHTML = prop.nombre;
    var link = listing.appendChild(document.createElement('td'));

    link.href = '#';
    link.className = 'title';
    link.innerHTML = prop.localidad_referencia;
}
}





function flyToStore(currentFeature) {
  // Geographic coordinates of the LineString
  var coordinates = currentFeature.geometry.coordinates[0];

  // Pass the first coordinates in the LineString to `lngLatBounds` &
  // wrap each coordinate pair in `extend` to include them in the bounds
  // result. A variation of this technique could be applied to zooming
  // to the bounds of multiple Points or Polygon geomteries - it just
  // requires wrapping all the coordinates with the extend method.
  var bounds = coordinates.reduce(function(bounds, coord) {
      return bounds.extend(coord);
  }, new mapboxgl.LngLatBounds(coordinates[0], coordinates[0]));

  map.fitBounds(bounds, {
      padding: 20
  });

/*
  map.flyTo({
    center: currentFeature.geometry.coordinates,
    zoom: 15
  });*/
$("#ugas-politica").css("display","none");
}
