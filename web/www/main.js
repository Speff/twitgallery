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

                    var orig_size_x = value["media_url_"+i+"_size_x"];
                    var orig_size_y = value["media_url_"+i+"_size_y"];
                    var AR = orig_size_x / orig_size_y;

                    orig_size_x = orig_size_x*0.25;
                    orig_size_y = orig_size_y*0.25;

                    var scaled_size_x = Math.round(orig_size_x/64.0)*64.0;
                    var scaled_size_y = scaled_size_x / AR;

                    $("#post_"+image_count).css("width", scaled_size_x);
                    $("#post_"+image_count).css("height", scaled_size_y);

                    var img_src = "<img src='"+value["media_url_"+i]+"'></img>";
                    $("#post_"+image_count).click({"img_src": img_src}, display_modal);
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
    console.log(input.data.img_src);
    $("#modal_fs").show();
    $("#picture_fs").html(input.data.img_src);
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

