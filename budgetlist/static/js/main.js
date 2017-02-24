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
//  $(document).ready(function () {
//     $('.DinamicTable').DataTable({
//         "ordering": false
//     });
// });
$(function() {              
   $('.datetimepicker').datetimepicker({
         format: 'DD/MM/YYYY'
   });
});