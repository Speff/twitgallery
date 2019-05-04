function display_images(user){
    $.post("/api/get_results", {"user_id": user}, function(data, status){
        $("#target").empty();

        $("#target").append("<div class='post_row'>");
        $("#target").append("<div class='post_col'>");
        var n_posted = 0;
        $.each(data.status, function(index, value){
            for(var i = 0; i < 4; i++){
                if(value["media_url_"+i] != null){
                    $("#target").append("<img src='"+value["media_url_"+i]+"' class='post'></img>");
                    n_posted = n_posted + 1;
                    if(n_posted % 6 == 0){
                        $("#target").append("</div><div class='post_col'>");
                    }
                }
            }

            if(index > 100) return false;
        });
        $("#target").append("</div>");
        $("#target").append("</div>");
    }, "json");
}

$(document).ready(function(){
    $("#user_input").val("@speff7");
    $("#process_user_input").click(function(){
        var user_to_process = $("#user_input").val();
        $.post("/api/process_user", {"user_id": user_to_process}, function(data, status){
            console.log(status);
            if(status == "success"){
                $("#process_user_result").text("User processed successfully");
            }
            else{
                $("#process_user_result").text("User processing failed");
            }
        });
    });
    $("#get_user_images").click(function(){
        var user_to_process = $("#user_input").val();
        display_images(user_to_process);
    });
});

