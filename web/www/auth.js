function close_window(){
    window.close();
}

$(document).ready(function(){
    var twit_params = window.location.search;
    let searchParams = new URLSearchParams(window.location.search)

    if(searchParams.has('oauth_token') && searchParams.has('oauth_verifier')){
        $.get("/api/auth_twit" + twit_params, function(data){
            if(data.status = "Success")
                $("#signed_in_message").html("Signed in successfully.<br><span class='hr_line'></span><br>This window will close automagically");
            else
                $("#signed_in_message").html("Sign in failed<br><span class='hr_line'></span>");

            setTimeout(close_window, 2000);
        });
    }
    else
        $("#signed_in_message").html("Sign in failed<br><span class='hr_line'></span>");
});

