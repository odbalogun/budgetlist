$(function() {
    $('.chart').easyPieChart({
    	animate: 2000,
        barColor:'#2C3E50',
        trackColor: '#f2f2f2'
    });

    //update instance after 5 sec

    // setTimeout(function() {
    //     $('.chart').data('easyPieChart').update(40);
    // }, 5000);
});

$(document).ready(function(){
    tinymce.init({
         selector:'textarea',
         toolbar: 'undo redo | insert | styleselect | bold italic | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent | link image',
     })
});

$(function() {              
   $('.datetimepicker').datetimepicker({
         format: 'DD/MM/YYYY'
   });
});

$(document).ready( function() {
    $('.alert').delay(5000).fadeOut();
});

$("input.money").maskMoney();
// $(".budgetForm").submit(function() {
//     alert()
//     $("input.money").maskMoney('destroy');
    
// });
$("form").submit(function(){
    $('input.money').maskMoney('unmasked')[0];
    console.log($('#input-value-id').val(value))
  });