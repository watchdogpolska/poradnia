window.addEventListener("load", function load(event){
    window.removeEventListener("load", load, false); 
    
    var headers = document.querySelectorAll('#feedback-header');
    Array.prototype.slice.call(headers).forEach(function(header){
     header.addEventListener('click', function(e){
       e.preventDefault();
       header.parentElement.classList.toggle('show');
   });
 });
},false);
