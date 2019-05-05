function display_images(user){
    $.post("/api/get_results", {"user_id": user}, function(data, status){
        $("#target").empty();

        $("#target").html("<div id='grid_01' class='grid'></div>");

        var image_count = 0;
        console.log(data);
        $.each(data.status, function(index, value){
            for(var i = 0; i < 4; i++){
                if(value["media_url_"+i] != null){
                    var post_html = "<div id='post_"+image_count+"' class='grid-item'>";
                    post_html += "<img class='main_image cover' src='" + value["media_url_"+i] + ":small'></img>";
                    post_html += "<img class='blur_image' src='" + value["media_url_"+i] + ":small'></img>";
                    post_html += "</div>";
                    $("#grid_01").append(post_html);

                    var new_element = $("#post_"+image_count);

                    var orig_size_x = value["media_url_"+i+"_size_x"];
                    var orig_size_y = value["media_url_"+i+"_size_y"];
                    var AR = orig_size_x / orig_size_y;
                    var mod_orig_size_x = orig_size_x*0.25;
                    var mod_orig_size_y = orig_size_y*0.25;
                    var scaled_size_x = Math.round(mod_orig_size_x/64.0)*64.0;
                    var scaled_size_y = scaled_size_x / AR;

                    console.log(value);

                    new_element.css("width", scaled_size_x);
                    new_element.css("height", scaled_size_y);

                    new_element.attr("data-"+"width", orig_size_x);
                    new_element.attr("data-"+"height", orig_size_y);
                    new_element.attr("data-"+"orig_width", scaled_size_x);
                    new_element.attr("data-"+"orig_height", scaled_size_y);
                    new_element.attr("data-"+"created_at", value["created_at"]);
                    new_element.attr("data-"+"post_id", value["post_id"]);
                    new_element.attr("data-"+"post_url", value["post_url"]);
                    new_element.attr("data-"+"text", value["text"]);
                    new_element.attr("data-"+"name", value["name"]);
                    new_element.attr("data-"+"screen_name", value["screen_name"]);
                    new_element.attr("data-"+"profile_image_url", value["profile_image_url"]);
                    new_element.attr("data-"+"possibly_sensitive", value["possibly_sensitive"]);
                    new_element.attr("data-"+"image", "<img src='"+value["media_url_"+i]+":large'></img>");

                    var img_src = 
                    new_element.click({"tag": new_element}, display_modal);
                    image_count += 1;
                }
            }
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
    $(".modal_content").css("width", current_post["data-width"].nodeValue);

    $("#picture_data").html("<h4><a href='" + current_post["data-post_url"].nodeValue + "'>" + current_post["data-name"].nodeValue + " (@" + current_post["data-screen_name"].nodeValue + ")</a></h4>");
    $("#picture_data").append("<h5>" + current_post["data-text"].nodeValue + "</h5>");
    $("#picture_fs").html(current_post["data-image"].nodeValue);
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

