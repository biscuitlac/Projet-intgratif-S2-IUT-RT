var url="http://10.66.88.1:8000/stats"
fetch(url).then(r => r.json()).then(interprete)
function interprete(d){
	DomBloq(d["top_blocked_domains"])
	reqTot(d["dns_queries"])
	reqBloqTot(d["blocked_filtering"])
	TauBloq(d["dns_queries"],d["blocked_filtering"])
	donut(d["top_blocked_domains"])
	bar(d["top_queried_domains"])
}
function DomBloq(dico){
	var effa = document.getElementById("top10-body")
	effa.innerHTML=""
	if(dico.length>=10){
		for(var i=0;i<10;i++){
			var cible = document.createElement("tr")
			for(cle in dico[i]){
				var element = document.createElement("td")
				element.innerHTML = i+1
				cible.appendChild(element)
				element = document.createElement("td")
				element.innerHTML = cle 
				cible.appendChild(element)
				element = document.createElement("td")
				element.innerHTML = dico[i][cle]
				cible.appendChild(element)
			}
			var corps = document.getElementById("top10-body")
			corps.appendChild(cible)
		}
	}else{
		for(var i=0;i<dico.length;i++){
			var cible = document.createElement("tr")
			for(cle in dico[i]){
				var element = document.createElement("td")
				element.innerHTML = i+1
				cible.appendChild(element)
				element = document.createElement("td")
				element.innerHTML = cle 
				cible.appendChild(element)
				element = document.createElement("td")
				element.innerHTML = dico[i][cle]
				cible.appendChild(element)
			}
			var corps = document.getElementById("top10-body")
			corps.appendChild(cible)
		}
	}
}
function ActuStat(dico){
	var url="http://10.66.88.1:8000/stats"
	fetch(url).then(r => r.json()).then(interprete)
}
function reqTot(dico){
	var somme = 0
	for(var i=0;i<dico.length;i++){
		somme += dico[i]
	}
	var cible = document.getElementById("kpi-total-requests")
	cible.innerHTML = somme
}
function reqBloqTot(dico){
	var somme = 0
	for(var i=0;i<dico.length;i++){
		somme += dico[i]
	}
	var cible = document.getElementById("kpi-blocked")
	cible.innerHTML = somme
}
	function TauBloq(dicoTot,dicoBloq){
	var sommeTot = 0
	for(var i=0;i<dicoTot.length;i++){
		sommeTot += dicoTot[i]
	}
	var sommeBloq = 0
	for(var i=0;i<dicoBloq.length;i++){
		sommeBloq += dicoBloq[i]
	}
	cible = document.getElementById("kpi-block-rate")
	if(sommeTot!=0){
	cible.innerHTML = Math.ceil((sommeBloq/sommeTot)*100) + "%"
	}else{
		cible.innerHTML = Nan
	}
}
function donut(dico){
	var doBloq = {labels:[],datasets:[{data: []}]} 
	for(var i=0;i<dico.length;i++){
		var donne = dico[i]
		for(cle in donne){
			doBloq["labels"].push(cle)
			doBloq["datasets"][0]["data"].push(donne[cle])
		}

	}
	new Chart("donut", {type: "doughnut", 
		data: doBloq,
		options: {}})
}
function bar(dico){
	var doBloq = {labels:[],datasets:[{data: []}]} 
	for(var i=0;i<dico.length;i++){
		var donne = dico[i]
		for(cle in donne){
			doBloq["labels"].push(cle)
			doBloq["datasets"][0]["data"].push(donne[cle])
		}

	}
	new Chart("bar", {type: "bar", 
		data: doBloq,
		options: {}})
}
var url = "https://safe.adguard.com/api/v2/safebrowsing//check?=webcast.tiktok.com"
fetch(url).then(r => r.json()).then(test)
function test(dico){
	console.log(dico)
}