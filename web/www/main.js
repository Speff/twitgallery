var offset = 0;
var image_count = 0;
var query_in_progress = false;
var no_more_images = false;
var search_user_changed = true;

function display_images(user){
    if(no_more_images){
        query_in_progress = false;
        return false;
    }

    $.post("/api/get_results", {"user_id": user, "offset": offset}, function(data, status){
        if(status != "success"){
            $("#end_results_target").text("End of images");
            query_in_progress = false;
            no_more_images = true;
            return false;
        }

        offset += 1;
        $("#target").append("<div id='grid_" + offset + "' class='grid'></div>");

        $.each(data.status, function(index, value){
            for(var i = 0; i < 4; i++){
                if(value["media_url_"+i] != null){
                    var post_html = "<div id='post_"+image_count+"' class='grid-item'>";
                    post_html += "<img class='main_image cover' src='" + value["media_url_"+i] + ":small'></img>";
                    post_html += "<img class='blur_image' src='" + value["media_url_"+i] + ":small'></img>";
                    post_html += "</div>";
                    $("#grid_"+offset).append(post_html);

                    var new_element = $("#post_"+image_count);

                    // Round grid sizes to minimize gaps
                    var orig_size_x = value["media_url_"+i+"_size_x"];
                    var orig_size_y = value["media_url_"+i+"_size_y"];
                    var AR = orig_size_x / orig_size_y;
                    var mod_orig_size_x = orig_size_x*0.25;
                    var mod_orig_size_y = orig_size_y*0.25;
                    var scaled_size_x = Math.round(mod_orig_size_x/64.0)*64.0;
                    var scaled_size_y = scaled_size_x / AR;
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

                    var img_src = new_element.click({"tag": new_element}, display_modal);
                    image_count += 1;
                }
            }
        });

        $('#grid_'+offset).packery({
            // options
            itemSelector: '.grid-item',
            stagger: 5,
        });

        query_in_progress = false;
    }, "json");
}

function display_modal(input){
    current_post = input.data.tag[0].attributes;
    $("#modal_fs").show();
    $(".modal_content").css("width", current_post["data-width"].nodeValue);

    $("#picture_data").html("<h4><a href='" + current_post["data-post_url"].nodeValue + "' target='_blank'>" + current_post["data-name"].nodeValue + " (@" + current_post["data-screen_name"].nodeValue + ")</a></h4>");
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

$(document).on("scroll", function(e){
    var scroll_pos = $(document).scrollTop() + $(window).height();
    if($(document).height() - scroll_pos < 200){
        if(query_in_progress == false){
            query_in_progress = true;
            var user_to_process = "@" + $("#user_input").text();
            display_images(user_to_process);
        }
    }
});

$(document).ready(function(){
    $("#user_input").text("speff7");
    $("#process_user_input").click(function(){
        if(query_in_progress == false){
            offset = 0;
            query_in_progress = true;
            $("#process_user_result").text("Processing User");
            var user_to_process = "@" + $("#user_input").text();
            $.post("/api/process_user", {"user_id": user_to_process}, function(data, status){
                query_in_progress = false;
                if(status == "success"){
                    $("#process_user_result").text("User processed successfully");
                    no_more_images = false;
                }
                else{
                    $("#process_user_result").text("User processing failed");
                }
            });
        }
        else; // Do nothing. There's already a query in progress
    });
    $("#get_user_images").click(function(){
        if(query_in_progress == false){
            if(search_user_changed) $("#target").empty();

            search_user_changed = false;
            query_in_progress = true;

            var user_to_process = "@" + $("#user_input").text();
            display_images(user_to_process);
        }
    });
    $("body").on('DOMSubtreeModified', "#user_input", function(){
        search_user_changed = true;
        no_more_images = false;
    });
    $("#input").dblclick(function(e){
        var selection = window.getSelection();
        var range = document.createRange();
        range.selectNodeContents($("#user_input").get(0));
        selection.removeAllRanges();
        selection.addRange(range);
    });
});

