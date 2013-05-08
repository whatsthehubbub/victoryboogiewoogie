// ready, go
$(document).ready(function(){

	// fancify logo
	$(".logo h1").lettering();

	// trigger bootstrap tooltip
	$('.tooltipster').tooltip();

	// fitvid videos
	$("article").fitVids();
	
});