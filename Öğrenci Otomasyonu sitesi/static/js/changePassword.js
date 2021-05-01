function validate() {
    var pass = document.getElementById("yeniParola").value;
    var cpass = document.getElementById("cpassword").value;
    if (pass == cpass) {
        return true;
    } else {
        alert("Parolalar eşleşmedi!");
        return false;
    }
}

