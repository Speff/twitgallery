function display_images(user){
    $.post("/api/get_results", {"user_id": user}, function(data, status){
        $("#target").empty();

        $("#target").html("<div id='grid_01' class='grid'></div>");

        var image_count = 0;
        $.each(data.status, function(index, value){
            for(var i = 0; i < 4; i++){
                if(value["media_url_"+i] != null){
                    var post_html = "<div id='post_"+image_count+"' class='grid-item'><img src='" + value["media_url_"+i] + "'></img></div>";
                    $("#grid_01").append(post_html);

                    $("#post_"+image_count).css("width", 0.3*(value["media_url_"+i+"_size_x"]));
                    $("#post_"+image_count).css("height", 0.3*(value["media_url_"+i+"_size_y"]));

                    image_count += 1;
                }
            }
            if(index > 20) return false;
        });

        $('#grid_01').packery({
            // options
            itemSelector: '.grid-item',
            stagger: 5
        });
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

