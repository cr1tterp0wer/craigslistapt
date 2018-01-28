 var links = function(){
  jQuery('tbody tr').each(function(i,e){

    var href = jQuery(jQuery(jQuery(e)).find('td')[4]).text()
    jQuery(jQuery(jQuery(e)).find('td')[4]).text('')
   jQuery(jQuery(jQuery(e)).find('td')[4]).append("<a href=" + href + ">See Now!</a>");
  });

 }
links();
