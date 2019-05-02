function main(){
    $(document).ready(function(){
        $.post("/api/get_results", {"screen_name": "@speff7"}, function(data, status){
            $("#target").text(data);
        }, "json");
    });
}

main();

