var url = "http://10.66.88.1:8000/ia/stats";
fetch(url).then(r => r.json()).then(carte_preums)
url = "http://10.66.88.1:8000/ia/vs-listes"
fetch(url).then(r => r.json()).then(carte_deums)
url = "http://10.66.88.1:8000/ia/blocks"
fetch(url).then(r => r.json()).then(appel_blocks)
url = "http://10.66.88.1:8000/ia/scores/distribution"
fetch(url).then(r => r.json()).then(repart_score)
url ="http://10.66.88.1:8000/stats"
fetch(url).then(r => r.json()).then(consStats)
url="http://10.66.88.1:8000/ia/blocks/recent"
fetch(url).then(r => r.json()).then(derdom)
function appel_blocks(d){
	donut(d)
	consBlock(d)
	carte_un()
}
function carte_preums(d){
	detect(d["total_bloques"])
	moyenne(d["score_moyen"])
	consStats(d)
}
function detect(cb){
	var cible = document.getElementById("kpi-ai-only")
	cible.innerHTML=cb 
}
function moyenne(sc){
	var cible = document.getElementById("kpi-confidence-avg")
	cible.innerHTML = sc
}
function carte_deums(d){
	var cible = document.getElementById("kpi-ai-gain")
	cible.innerHTML = d["ia_contribution_pct"] + " %"
	iavslist(d)
}
function iavslist(dico){
	var doBloq = {labels:[],datasets:[{data: [],label: "Domaines bloqués"}]} 
	var cle = Object.keys(dico)
	for(var i=0;i<2;i++){
		doBloq["labels"].push(cle[i])
		doBloq["datasets"][0]["data"].push(dico[cle[i]])
	}

	new Chart("bar_groupe", {type: "bar", 
		data: doBloq,
		options: {}})
}
function donut(dico){
	var doBloq = {labels:[],datasets:[{data: []}]} 
	for(var i=0;i<dico["total"];i++){
		doBloq["labels"].push(dico["results"][i]["domain"])
		doBloq["datasets"][0]["data"].push(1)

	}
	new Chart("donut", {type: "doughnut", 
		data: doBloq,
		options: {}})

}
function repart_score(dico){
	var doBloq = {labels:[],datasets:[{data: [],label: "Nombre de Domaines"}]} 
	for(var i=0;i<dico["tranches"].length;i++){
		doBloq["labels"].push(dico["tranches"][i]["tranche"])
		doBloq["datasets"][0]["data"].push(dico["tranches"][i]["count"])

	}
	new Chart("barre_conf", {type: "bar", 
		data: doBloq,
		options: {}})
}
var stats = {}
function consStats(d){
	stats = d["top_blocked_domains"]
}
var bloq = {}
function consBlock(d){
	bloq = d["results"]
}
function iauniq(dom_ia,dom_ls){
	var cle = [];
	for(var j=0;j<dom_ls;j++){
		cle[j] = Object.keys(dom_ls[j])
	}
	var dom_un = dom_ia.length;
	for(var i=0;i<dom_ia.length;i++){
		for(var j=0;j<dom_ls;j++){
			if(dom_ia[i]["domain"]==cle[j]){
				dom_un -= 1
			}
		}
	}
	return dom_un
}
function carte_un(){
	var nb = iauniq(bloq,stats)
	var cible = document.getElementById("kpi-new-threats")
	cible.innerHTML = nb
}
function derdom(dico){
	var corps = document.getElementById("ai-detections-body")
		for(var i=0;i<dico["results"].length;i++){
			var cible = document.createElement("tr")
			var element = document.createElement("td")
			element.innerHTML = dico["results"][i]["domain"]
			cible.appendChild(element)
			element = document.createElement("td")
			element.innerHTML = dico["results"][i]["score"]
			cible.appendChild(element)
			element = document.createElement("td")
			element.innerHTML = dico["results"][i]["date"]
			cible.appendChild(element)
			corps.appendChild(cible)
		}
}
