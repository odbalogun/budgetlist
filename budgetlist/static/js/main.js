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


$(document).ready( function() {
    $('.alert').delay(5000).fadeOut();
});

$("input.money").maskMoney();


$('.collaptable').aCollapTable({ 

    // the table is collapased at start
    startCollapsed: true,

    // the plus/minus button will be added like a column
    addColumn: true, 

    // The expand button ("plus" +)
    plusButton: "<button title='Show Subtask' class='viewBtn'><i class='fa fa-chevron-right' aria-hidden='true'></i></button>", 

    // The collapse button ("minus" -)
    minusButton: "<button title='Hide Subtask' class='viewBtn'><i class='fa fa-chevron-down' aria-hidden='true'></i></button>" 
  
});

$(document).ready(function() {
  $(".multiselect").select2();
});

$(document).ready(function() {
    $('.dataTable').DataTable();
} );


var doc = new jsPDF();
var specialElementHandlers = {
    '#editor': function (element, renderer) {
        return true;
    }
};

$('.printPDF').click(function () {
    doc.fromHTML($('#mainPage').html(), 15, 15, {
        'width': 170,
            'elementHandlers': specialElementHandlers
    });
    doc.save('budgetHistory.pdf');
});

$('.printMe').click(function(){
     window.print();
});

$( function() {
    $( ".datepicker" ).datepicker({
      changeMonth: true,
      changeYear: true,
      dateFormat: "dd/mm/yy",
      altFormat: 'yy-mm-dd'
    });
  } );