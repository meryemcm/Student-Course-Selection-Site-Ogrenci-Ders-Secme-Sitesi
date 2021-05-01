function validate() {
    var pass = document.getElementById("parola").value;
    var cpass = document.getElementById("cpassword").value;
    if (pass == cpass) {
        return true;
    } else {
        alert("Parolalar eşleşmedi!");
        return false;
    }
}


