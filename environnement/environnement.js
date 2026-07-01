var url = "http://10.66.88.1:8000/stats/queried-by-category"
fetch(url).then(r => r.json()).then(donne_barre)
url = "http://10.66.88.1:8000/stats/blocked-by-category";
fetch(url).then(r => r.json()).then(interprete)
function interprete(d){
	donBloq(d["categories"])
	graphe(d["categories"])
	var donnee = volDonnee(d["categories"])
	donneApre(donnee)
	duration_apres(d["categories"])
	codeux()
}
url = "http://10.66.88.1:8000/stats";
fetch(url).then(r => r.json()).then(barre)
function barre(d){
	trafic(d)
}
function donne_barre(d){
	var donne_totale = volDonnee(d["categories"])
	donneTot(donne_totale)
	duration_avant(d["categories"])

}
var estConso = {
	"pub": 1,
	"tracker":0.15,
	"reseaux":0.5,
	"Paris":1,
	"Crypto":2.5,
	"Stream":3,
	"autre":1
}
function volDonnee(dico){
	var somme = 0;
	if(dico["Tracking & Analytics"] != undefined){
		for(var i=0; i<dico["Tracking & Analytics"].length;i++){
			somme += dico["Tracking & Analytics"][i]["count"]*estConso["tracker"]
		}
	}

	if(dico["Publicité"] != undefined){
		for(var i=0; i<dico["Publicité"].length;i++){
			somme += dico["Publicité"][i]["count"]*estConso["pub"]
		}
	}

	if(dico["Réseaux sociaux"] != undefined){
		for(var i=0; i<dico["Réseaux sociaux"].length;i++){
			somme += dico["Réseaux sociaux"][i]["count"]*estConso["reseaux"]
		}
	}

	if(dico["Contenu adulte"] != undefined){
		for(var i=0; i<dico["Contenu adulte"].length;i++){
			somme += dico["Contenu adulte"][i]["count"]*estConso["Stream"]
		}
	}

	if(dico["Jeux & Paris"] != undefined){
		for(var i=0; i<dico["Jeux & Paris"].length;i++){
			somme += dico["Jeux & Paris"][i]["count"]*estConso["Paris"]
		}
	}

	if(dico["Streaming & Médias"] != undefined){
		for(var i=0; i<dico["Streaming & Médias"].length;i++){
			somme += dico["Streaming & Médias"][i]["count"]*estConso["Stream"]
		}
	}

	if(dico["Cryptomonnaie & Mining"] != undefined){
		for(var i=0; i<dico["Cryptomonnaie & Mining"].length;i++){
			somme += dico["Cryptomonnaie & Mining"][i]["count"]*estConso["Crypto"]
		}
	}

	if(dico["Malware & Phishing"] != undefined){
		for(var i=0; i<dico["Malware & Phishing"].length;i++){
			somme += dico["Malware & Phishing"][i]["count"]*estConso["autre"]
		}
	}

	if(dico["Autre"] != undefined){
		for(var i=0; i<dico["Autre"].length;i++){
			somme += dico["Autre"][i]["count"]*estConso["autre"]
		}
	}
	return somme
}
function donBloq(dico){
	var somme = volDonnee(dico)
	var cible = document.getElementById("eco-data-number")
	cible.innerHTML = Math.floor(somme)
	cible = document.getElementById("eco-co2-number")
	var somCarb = somme * 0.089
	cible.innerHTML = Math.floor(somCarb)
}
function trafic(dico){
	var cible = document.getElementById("val-dns-before")
	var reqDNS = dico["num_dns_queries"]
	cible.innerHTML = reqDNS
	cible = document.getElementById("val-dns-after")
	var reqBloq = dico["num_blocked_filtering"]
	cible.innerHTML = reqDNS - reqBloq 
	var ratio = ((reqDNS-reqBloq)/reqDNS)*100
	cible = document.getElementById("badge-dns-gain")
	cible.innerHTML = Math.ceil(100-ratio) + " %" 
	cible = document.getElementById("bar-dns-after")
	cible.setAttribute("style","width:"+ratio+"%; height:8px; border-radius:4px")

}
function graphe(dico){
	var donnedom = [];
	var donnesite = [];
	if(dico["Tracking & Analytics"] != undefined){
		for(var i=0; i<dico["Tracking & Analytics"].length;i++){
			donnedom.push(dico["Tracking & Analytics"][i]["domain"])
			donnesite.push(dico["Tracking & Analytics"][i]["count"]*estConso["tracker"])
		}
	}
	if(dico["Publicité"] != undefined){
		for(var i=0; i<dico["Publicité"].length;i++){
			donnedom.push(dico["Publicité"][i]["domain"])
			donnesite.push(dico["Publicité"][i]["count"]*estConso["pub"])
		}
	}
	if(dico["Réseaux sociaux"] != undefined){
		for(var i=0; i<dico["Réseaux sociaux"].length;i++){
			donnedom.push(dico["Réseaux sociaux"][i]["domain"])
			donnesite.push(dico["Réseaux sociaux"][i]["count"]*estConso["reseaux"])
		}
	}
	if(dico["Contenu adulte"] != undefined){
		for(var i=0; i<dico["Contenu adulte"].length;i++){
			donnedom.push(dico["Contenu adulte"][i]["domain"])
			donnesite.push(dico["Contenu adulte"][i]["count"]*estConso["Stream"])
		}
	}
	if(dico["Jeux & Paris"] != undefined){
		for(var i=0; i<dico["Jeux & Paris"].length;i++){
			donnedom.push(dico["Jeux & Paris"][i]["domain"])
			donnesite.push(dico["Jeux & Paris"][i]["count"]*estConso["Paris"])
		}
	}
	if(dico["Streaming & Médias"] != undefined){
		for(var i=0; i<dico["Streaming & Médias"].length;i++){
			donnedom.push(dico["Streaming & Médias"][i]["domain"])
			donnesite.push(dico["Streaming & Médias"][i]["count"]*estConso["Stream"])
		}
	}
	if(dico["Cryptomonnaie & Mining"] != undefined){
		for(var i=0; i<dico["Cryptomonnaie & Mining"].length;i++){
			donnedom.push(dico["Cryptomonnaie & Mining"][i]["domain"])
			donnesite.push(dico["Cryptomonnaie & Mining"][i]["count"]*estConso["Crypto"])
		}
	}
	if(dico["Malware & Phishing"] != undefined){
		for(var i=0; i<dico["Malware & Phishing"].length;i++){
			donnedom.push(dico["Malware & Phishing"][i]["domain"])
			donnesite.push(dico["Malware & Phishing"][i]["count"]*estConso["autre"])
		}
	}
	if(dico["Autre"] != undefined){
		for(var i=0; i<dico["Autre"].length;i++){
			donnedom.push(dico["Autre"][i]["domain"])
			donnesite.push(dico["Autre"][i]["count"]*estConso["autre"])
		}
	}
	var BpD = {labels:donnedom,datasets:[{backgroundColor: ["blue"],label: "Requêtes bloquées",data: donnesite}]};
	new Chart("barre", {type: "bar", 
		data: BpD,
		options: {
			title: {
      display: false,
    }}})
}
function donneTot(donTo){
	var cible = document.getElementById("val-data-before")
	cible.innerHTML = donTo
}
function donneApre(donBlo){
	var cible = document.getElementById("val-data-before")
	var donTo = cible.innerHTML
	cible = document.getElementById("val-data-after")
	cible.innerHTML = donTo - donBlo
	var ratio = ((donTo - donBlo)/donTo)*100
	cible = document.getElementById("badge-data-gain")
	cible.innerHTML = Math.ceil(100-ratio) + " %" 
	cible = document.getElementById("bar-data-after")
	cible.setAttribute("style","width:"+ratio+"%; height:8px; border-radius:4px")
}
function codeux(){
	var cible = document.getElementById("val-data-before")
	var donTo = cible.innerHTML
	cible = document.getElementById("val-co2-before")
	cible.innerHTML = Math.round(donTo*0.089)
	cible = document.getElementById("val-data-after")
	donTo = cible.innerHTML
	cible = document.getElementById("val-co2-after")
	cible.innerHTML = Math.round(donTo*0.089)
	cible = document.getElementById("badge-data-gain")
	var co2 = cible.innerHTML
	cible = document.getElementById("badge-co2-gain")
	cible.innerHTML = co2
	co2 = parseInt(co2.charAt(0) + co2.charAt(1))
	cible = document.getElementById("bar-co2-after")
	co2 = 100 - co2
	cible.setAttribute("style","width:"+co2+"%; height:8px; border-radius:4px")
}
function duration_avant(dico){
	var somme = 0
	var c = 0
	for(cle in dico){
		for(var i=0;i<dico[cle].length;i++){
			c++
			somme += dico[cle][i]["duration_ms"]
		}
	}
	somme = somme/c;
	var cible = document.getElementById("val-perf-before")
	cible.innerHTML = Math.round(somme)
}
function duration_apres(dico){
	var cible = document.getElementById("val-perf-before")
	var somme_av = cible.innerHTML
	var somme_apres = 0
	var c = 0
	for(cle in dico){
		for(var i=0;i<dico[cle].length;i++){
			c++
			somme_apres += dico[cle][i]["duration_ms"]
		}
	}
	somme_apres = somme_apres/c;
	cible = document.getElementById("val-perf-after")
	cible.innerHTML = Math.round(somme_apres)
	cible = document.getElementById("badge-perf-gain")
	var pourcentage = Math.round(((somme_av-somme_apres)/somme_av)*100)
	cible.innerHTML = pourcentage + " %"
	cible = document.getElementById("bar-perf-after")
	pourcentage = 100 - pourcentage
	cible.setAttribute("style","width:"+pourcentage+"%; height:8px; border-radius:4px")
}