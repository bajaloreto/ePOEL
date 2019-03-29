
<script>

$(document).ready(function(){
  $('#myModal').modal('show');
  $("#diagnostico-card").click(function(){
    if ($("#diagnostico-card").hasClass( "activo" )) {
      $("#diagnostico-card").removeClass("activo");
    }
    else {
      $("#diagnostico-card").addClass("activo");
    }

    $("#diagnostico").collapse('toggle');
    $("#propuesta,#ugas").collapse('hide');
      $("#propuesta-card,#ugas-card").removeClass("activo");
    });

  $("#propuesta-card").click(function(){
    if ($("#propuesta-card").hasClass( "activo" )) {
      $("#propuesta-card").removeClass("activo");
    }
    else {
      $("#propuesta-card").addClass("activo");
    }

    $("#propuesta").collapse('toggle');
    $("#diagnostico,#ugas").collapse('hide');
      $("#diagnostico-card,#ugas-card").removeClass("activo");
    });

  $("#ugas-card").click(function(){
    if ($("#ugas-card").hasClass( "activo" )) {
      $("#ugas-card").removeClass("activo");
    }
    else {
      $("#ugas-card").addClass("activo");
    }

    $("#ugas").collapse('toggle');
    $("#diagnostico,#propuesta").collapse('hide');
      $("#diagnostico-card,#propuesta-card").removeClass("activo");
    });
    $("input[type=radio]").on('click',function(){
      $("#datos").css("display","none")
      var radio= this.id;
    switch (radio) {
      case "aprovechamiento_sustentable":{
        map.setLayoutProperty('aprovechamiento-sustentable', 'visibility','visible');
        map.setLayoutProperty('aprovechamiento_sustentable_lineas', 'visibility','visible');
        buildLocationList(aprovechaminto_sustentable);
        $("#ugas-politica").css("display","inherit");
      }
        break;
        case "preservacion":{
          map.setLayoutProperty('preservacion', 'visibility','visible');
          map.setLayoutProperty('preservacion_lineas', 'visibility','visible');
          buildLocationList(preservacion);
          $("#ugas-politica").css("display","inherit");
        }
          break;
          case "conservacion":{
            map.setLayoutProperty('conservacion', 'visibility','visible');
            map.setLayoutProperty('conservacion_lineas', 'visibility','visible');
            buildLocationList(conservacion);
            $("#ugas-politica").css("display","inherit");
          }
            break;
            case "restauracion":{
              map.setLayoutProperty('restauracion', 'visibility','visible');
              map.setLayoutProperty('restauracion_lineas', 'visibility','visible');
              buildLocationList(restauracion);
              $("#ugas-politica").css("display","inherit");
            }
              break;
      default:

    }
  });

$("#toggle_principal").click(function(){
  alert("hi");
  $("#menu_principal").fadeToggle();

});



});
</script>
