// TODO: Create invisible div on existing grid before pulling new set
var offset = 0;
var image_count = 0;
var query_in_progress = false;
var no_more_images = false;
var selected_image_fs = 0;
var images_displayed = "favorites"

var is_mobile = false;

function check_if_signed_in(){
    $.get("/api/verify_twit", function(data){
        console.log(data);
        if(data.status == "Authenticated"){
            $("#sign_in").hide();
        }
        else{
            $("#sign_in").show();
            $("#sign_in").click(sign_in);
        }
    })
}

function sign_in(){
    $.get("/api/get_auth_url", function(data){
        var auth_url = data.auth_url;

        var spawned_window = window.open(auth_url, "_blank" , {
            "menubar": "no",
            "status": "no",
            "toolbar": "no"
        });

        var pollTimer = window.setInterval(function() {
            if (spawned_window.closed !== false){
                window.clearInterval(pollTimer);
                console.log("Child window closed");
                check_if_signed_in();
            }
        }, 200);
    });
}

function display_images(user){
    if(no_more_images){
        query_in_progress = false;
        return false;
    }

    $.post("/api/get_user_statuses", {"user_id": user, "offset": offset, "type": images_displayed}, function(data, status){
        if(status != "success"){
            $("#end_results_target").text("The End");
            query_in_progress = false;
            no_more_images = true;
            return false;
        }

        if(data.status == "session not found" || data.status == "credentials no longer valid"){
            console.log("No session found");
            $("#sign_in > img").css("animation", "shadow-pulse 1s infinite");
            query_in_progress = false;
            return false;
        }

        offset += 1;

        $.each(data.status, function(index, value){
            for(var i = 0; i < 4; i++){
                if(value["media_url_"+i] != null){
                    var post_html = "<div id='post_"+image_count+"' class='grid-item'>";
                    post_html += "<p class='loading_message'>Loading...</p>";
                    post_html += "<img class='main_image cover' src='" + value["media_url_"+i].replace("http:", "https:") + ":small'></img>";

                    if(is_mobile);
                    else
                        post_html += "<img class='blur_image' src='" + value["media_url_"+i].replace("http:", "https:") + ":small'></img>";

                    post_html += "</div>";
                    $("#grid_invis").append(post_html);

                    $("#post_"+image_count + " > .main_image").on('load', function(e){
                        $(e.target).parent().children(".loading_message").hide();
                    });

                    var new_element = $("#post_"+image_count);

                    // Round grid sizes to minimize gaps
                    var orig_size_x = value["media_url_"+i+"_size_x"];
                    var orig_size_y = value["media_url_"+i+"_size_y"];
                    var AR = orig_size_x / orig_size_y;
                    var mod_orig_size_x = orig_size_x*0.25;
                    var mod_orig_size_y = orig_size_y*0.25;
                    var scaled_size_x = Math.round(mod_orig_size_x/512.0)*512.0;
                    if(scaled_size_x < 288) scaled_size_x = 288;
                    if(scaled_size_x > 576) scaled_size_x = 576;
                    var scaled_size_y = scaled_size_x / AR;
                    if(scaled_size_y < 288){
                        scaled_size_y = 288;
                        scaled_size_x = scaled_size_y * AR;
                    }
                    if(scaled_size_y > 576){
                        scaled_size_y = 576;
                        scaled_size_x = scaled_size_y * AR;
                    }
                    if(is_mobile){
                        scaled_size_x = scaled_size_x * 0.4;
                        scaled_size_y = scaled_size_y * 0.4;
                    }
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

        // Sort by area to optimize packing
        $("div#grid_invis > div").sort(function(a,b){
            if(is_mobile){
                var var_a = parseInt($(a).attr("data-height"));
                var var_b = parseInt($(b).attr("data-height"));
                return (var_a > var_b) ? -1 : (var_a < var_b) ? 1 : 0;
            }
            else{
                var var_a = parseInt($(a).attr("data-height"))*parseInt($(a).attr("data-width"));
                var var_b = parseInt($(b).attr("data-height"))*parseInt($(b).attr("data-width"));
                return (var_a > var_b) ? -1 : (var_a < var_b) ? 1 : 0;
            }
        }).appendTo("div#grid_invis");

        $.each($("div#grid_invis > div"), function(index, elem){
            $("#grid").append(elem)
                .packery('appended', elem)
        });


        query_in_progress = false;
    }, "json");
}

function display_modal(input){
    selected_image_fs = 0;
    current_post = input.data.tag[0].attributes;
    $("#modal_fs").show();

    $("#picture_data").html("<h4 class='modal_author'><a href='" + current_post["data-post_url"].nodeValue + "' target='_blank'>" + current_post["data-name"].nodeValue + " (@" + current_post["data-screen_name"].nodeValue + ")</a><span id='search_selected'> <br>[Search user] </span></h4>")
        .append()
        .append("<br><h5>" + current_post["data-text"].nodeValue + "</h5>");
    $("#picture_fs").html(current_post["data-image"].nodeValue)
    $("#picture_fs > img").css("max-width", "100vw");
    $("#picture_fs > img").css("max-height", $(window).height() - $("#picture_data").height());

    var hidden_div = $("<div style='overflow:scroll;position:absolute;top:-99999px'></div>").appendTo("body");
    var scrollbar_width = hidden_div.prop("offsetWidth") - hidden_div.prop("clientWidth");
    hidden_div.remove();

    $("#search_selected").click(function(){
        $("#modal_fs").hide();
        $("#user_input").text(current_post["data-screen_name"].nodeValue);
        $("#grid").remove();
        window.scrollTo({ top: 0, behavior: 'smooth' })

    });
};


$(document).click(function(e){
    if(e.target == $("#picture_fs > img")[0]){
        if(selected_image_fs == 0){
            selected_image_fs = 1;
            $("#picture_fs > img").css("max-width", "");
            $("#picture_fs > img").css("max-height", "");
        }
        else if(selected_image_fs == 1){
            selected_image_fs = 0;
            $("#modal_fs").hide();
        }
    }
    else if(e.target == $("#modal_fs")[0]) $("#modal_fs").hide();
    else if(e.target == $("#picture_data")[0]) $("#modal_fs").hide();
    else if(e.target == $("#picture_fs")[0]) $("#modal_fs").hide();
});

$(document).keyup(function(e) {
    if(e.key == "Escape") $("#modal_fs").hide();
});

$(document).on("scroll", function(e){
    var scroll_pos = $(document).scrollTop() + $(window).height();
    //$("#page_console").text(scroll_pos + " / " + $(document).height() + " is_mobile: " + is_mobile);
    if($("#footer").offset().top - scroll_pos < 700){
        if(query_in_progress == false){
            query_in_progress = true;
            var user_to_process = "@" + $("#user_input").text();
            display_images(user_to_process);
        }
    }
});

function check_if_mobile() {
    try {
        if(/Android|webOS|iPhone|iPad|iPod|pocket|psp|kindle|avantgo|blazer|midori|Tablet|Palm|maemo|plucker|phone|BlackBerry|symbian|IEMobile|mobile|ZuneWP7|Windows Phone|Opera Mini/i.test(navigator.userAgent)) {
            return true;
        };
        return false;
    } catch(e){ console.log("Error in isMobile"); return false; }
}

function get_user_statuses(event){
    images_displayed = event.data.pt;
    if(query_in_progress == false){
        $("#target").empty();

        offset = 0;
        no_more_images = false;
        query_in_progress = true;
        var user_to_process = "@" + $("#user_input").text();

        $("#target").append("<div id='grid' class='grid'></div>");
        $("#grid").packery({
            // options
            itemSelector: '.grid-item',
            stagger: 5,
        });

        display_images(user_to_process);
    }
}

$(document).ready(function(){
    is_mobile = check_if_mobile();
    check_if_signed_in();

    $("#user_input").text("speff7");
    $("#get_user_favorites").click({"pt": "favorites"}, get_user_statuses);
    $("#get_user_posts").click({"pt": "posts"}, get_user_statuses);
    $("body").on('DOMSubtreeModified', "#user_input", function(){
        no_more_images = false;
    });
    $("#input").click(function(){
        $("#user_input").focus();
        $("#input").css({"transition": "all 0.1s", "border-bottom": "1px solid #aaaaaa"});
        $("#input").css({"border-right": "1px solid #aaaaaa"});
    });
    $("#user_input").focusout(function(){
        $("#input").css({"transition": "all 0.1s", "border-bottom": "1px solid transparent"});
        $("#input").css({"border-right": "1px solid transparent"});
    });
    $("#input").dblclick(function(e){
        var selection = window.getSelection();
        var range = document.createRange();
        range.selectNodeContents($("#user_input").get(0));
        selection.removeAllRanges();
        selection.addRange(range);
    });
    $("span#user_input").keypress(function(e){
        if(e.keyCode === 10 || e.keyCode === 13) e.preventDefault();
    });
});

