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
   // $('.datetimepicker').datetimepicker({
   //       format: 'DD/MM/YYYY'
   // });
   // $('.datetimepicker').pickadate()
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

$('.collaptable').aCollapTable({ 

    // the table is collapased at start
    startCollapsed: true,

    // the plus/minus button will be added like a column
    addColumn: true, 

    // The expand button ("plus" +)
    plusButton: "<button title='Show Subtask' class='viewBtn'><i class='fa fa-chevron-right' aria-hidden='true'></i></button>", 

    // The collapse button ("minus" -)
    minusButton: "<button title='Hide Subtask' class='viewBtn'><i class='fa fa-chevron-up' aria-hidden='true'></i></button>" 
  
});

$(".multiSelect").chosen();