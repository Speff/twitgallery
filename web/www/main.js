function display_images(user){
    $.post("/api/get_results", {"user_id": user}, function(data, status){
        $("#target").empty();

        $("#target").html("<div id='grid_01' class='grid'></div>");

        var image_count = 0;
        $.each(data.status, function(index, value){
            for(var i = 0; i < 4; i++){
                if(value["media_url_"+i] != null){
                    var post_html = "<div id='post_"+image_count+"' class='grid-item'>";
                    post_html += "<img class='main_image' src='" + value["media_url_"+i] + "'></img>";
                    post_html += "<img class='blur_image' src='" + value["media_url_"+i] + "'></img>";
                    post_html += "</div>";
                    $("#grid_01").append(post_html);

                    var new_element = $("#post_"+image_count);

                    var orig_size_x = value["media_url_"+i+"_size_x"];
                    var orig_size_y = value["media_url_"+i+"_size_y"];
                    var AR = orig_size_x / orig_size_y;
                    orig_size_x = orig_size_x*0.25;
                    orig_size_y = orig_size_y*0.25;
                    var scaled_size_x = Math.round(orig_size_x/64.0)*64.0;
                    var scaled_size_y = scaled_size_x / AR;

                    new_element.css("width", scaled_size_x);
                    new_element.css("height", scaled_size_y);

                    new_element.attr("data-"+"created_at", value["created_at"]);
                    new_element.attr("data-"+"user_favorites.post_id", value["user_favorites.post_id"]);
                    new_element.attr("data-"+"text", value["text"]);
                    new_element.attr("data-"+"name", value["name"]);
                    new_element.attr("data-"+"user_favorites.screen_name", value["user_favorites.screen_name"]);
                    new_element.attr("data-"+"profile_image_url", value["profile_image_url"]);
                    new_element.attr("data-"+"possibly_sensitive", value["possibly_sensitive"]);
                    new_element.attr("data-"+"image", "<img src='"+value["media_url_"+i]+"'></img>");

                    var img_src = 
                    new_element.click({"tag": new_element}, display_modal);
                    image_count += 1;
                }
            }
            if(index > 20) return false;
        });

        $('#grid_01').packery({
            // options
            itemSelector: '.grid-item',
            stagger: 5,
        });
    }, "json");
}

function display_modal(input){
    current_post = input.data.tag[0].attributes;
    console.log(current_post["data-image"].nodeValue);
    $("#modal_fs").show();
    $("#picture_data").html("Test data");
    $("#picture_fs").append(current_post["data-image"].nodeValue);
};

$(document).click(function(e){
    if(e.target == $("#modal_fs")[0]){
        $("#modal_fs").hide();
    }
});

$(document).keyup(function(e) {
    if(e.key == "Escape") $("#modal_fs").hide();
});

$(document).ready(function(){
    $("#user_input").val("@speff7");
    $("#process_user_input").click(function(){
        $("#process_user_result").empty();
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

