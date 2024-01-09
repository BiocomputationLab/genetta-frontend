function handle_submit_input(id) {
    $('#submit_forms').children('div').each(function () {
        $("#" + this.id).not("#" + id).slideUp();
    });
    $("#" + id).slideToggle();
}


$(document).ready(function () {
    if ($('#staticBackdrop').length) {
        $('#staticBackdrop').modal('show');
    }
});



document.getElementById('query_bar_tg').addEventListener('change', function () {

    var divs = document.getElementById("query_bar_descriptions").children;
    for (var i = 0; i < divs.length; i++) {
        //do something to each div like
        if (divs[i].id == this.value) {
            divs[i].style.display = "initial";
        } else {
            divs[i].style.display = "none";
        }
    }
    var example = document.getElementById(this.value + "_examples").innerText
    document.getElementById("query_bar").placeholder = example

});