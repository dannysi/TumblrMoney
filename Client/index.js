console.log("file start");
var myImg = React.createClass({
    render: function() {
        Console.log("render func");
        return (<h2>kaki</h2>);
        //return (<img src = "https://scontent.cdninstagram.com/t51.2885-15/sh0.08/e35/p640x640/17334026_201734506980848_637753543389872128_n.jpg"/>);
    }
});

console.log("render func");
ReactDOM.render(
    <div>
    MOSHE
    <myImg> </myImg>
    <p> barboor </p>
     </div>,
    document.getElementById("Main")
);
console.log("DONE");
