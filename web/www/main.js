function main(){
   //.post("/api/process_user", {"user_id": "@speff7"}, function(data, status){
        $.post("/api/get_results", {"user_id": "@speff7"}, function(data, status){
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

                if(index > 10) return false;
            });
            $("#target").append("</div>");
            $("#target").append("</div>");
        }, "json");
    //});
}

$(document).ready(function(){
    $("#user_input").val("@speff7");
    main();
});

