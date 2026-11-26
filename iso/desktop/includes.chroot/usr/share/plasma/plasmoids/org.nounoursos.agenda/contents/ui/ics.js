// Lecture d'un calendrier ICS (iCloud, Google, Nextcloud…) : événements à venir.
// Gère les dates entières (jour), les heures UTC/locales, et les répétitions simples
// (RRULE FREQ=DAILY/WEEKLY/MONTHLY/YEARLY avec INTERVAL, COUNT, UNTIL, BYDAY) + EXDATE.
.pragma library

function deplier(texte) {
    // Lignes repliées : une ligne qui commence par une espace continue la précédente
    return texte.replace(/\r\n/g, "\n").replace(/\n[ \t]/g, "");
}

function lireDate(valeur, params) {
    var v = valeur.trim();
    var m = v.match(/^(\d{4})(\d{2})(\d{2})(?:T(\d{2})(\d{2})(\d{2})(Z)?)?$/);
    if (!m) return null;
    var journee = !m[4] || (params && params.indexOf("VALUE=DATE") >= 0 && !m[4]);
    if (!m[4]) return { date: new Date(+m[1], +m[2] - 1, +m[3]), journee: true };
    if (m[7]) return { date: new Date(Date.UTC(+m[1], +m[2] - 1, +m[3], +m[4], +m[5], +m[6])), journee: false };
    return { date: new Date(+m[1], +m[2] - 1, +m[3], +m[4], +m[5], +m[6]), journee: false };
}

function texteICS(v) {
    return v.replace(/\\n/gi, " ").replace(/\\,/g, ",").replace(/\;/g, ";").replace(/\\\\/g, "\\").trim();
}

function evenements(texte) {
    var lignes = deplier(texte).split("\n");
    var out = [], ev = null;
    for (var i = 0; i < lignes.length; i++) {
        var l = lignes[i];
        if (l === "BEGIN:VEVENT") { ev = { exdates: [] }; continue; }
        if (l === "END:VEVENT") { if (ev && ev.debut && ev.titre !== undefined) out.push(ev); ev = null; continue; }
        if (!ev) continue;
        var dp = l.indexOf(":");
        if (dp < 0) continue;
        var tete = l.substring(0, dp), val = l.substring(dp + 1);
        var nom = tete.split(";")[0].toUpperCase(), params = tete.substring(nom.length);
        if (nom === "SUMMARY") ev.titre = texteICS(val);
        else if (nom === "LOCATION") ev.lieu = texteICS(val);
        else if (nom === "DTSTART") { var d = lireDate(val, params); if (d) { ev.debut = d.date; ev.journee = d.journee; } }
        else if (nom === "DTEND") { var f = lireDate(val, params); if (f) ev.fin = f.date; }
        else if (nom === "RRULE") ev.rrule = val;
        else if (nom === "EXDATE") val.split(",").forEach(function (x) { var e = lireDate(x, params); if (e) ev.exdates.push(e.date.getTime()); });
        else if (nom === "STATUS" && val.trim() === "CANCELLED") ev.annule = true;
    }
    return out.filter(function (e) { return !e.annule; });
}

var JOURS = { SU: 0, MO: 1, TU: 2, WE: 3, TH: 4, FR: 5, SA: 6 };

function occurrences(ev, debut, fin) {
    var res = [];
    var duree = ev.fin ? ev.fin - ev.debut : 0;
    function ajouter(d) {
        if (ev.exdates.indexOf(d.getTime()) >= 0) return;
        var finOcc = new Date(d.getTime() + duree);
        if (finOcc >= debut && d < fin) res.push({ titre: ev.titre || "(sans titre)", lieu: ev.lieu || "", debut: d, fin: finOcc, journee: ev.journee });
    }
    if (!ev.rrule) { ajouter(ev.debut); return res; }
    var r = {};
    ev.rrule.split(";").forEach(function (p) { var kv = p.split("="); r[kv[0].toUpperCase()] = kv[1]; });
    var freq = r.FREQ, pas = parseInt(r.INTERVAL || "1"), compte = r.COUNT ? parseInt(r.COUNT) : -1;
    var jusqu = r.UNTIL ? lireDate(r.UNTIL, "").date : null;
    var jours = r.BYDAY ? r.BYDAY.split(",").map(function (j) { return JOURS[j.slice(-2)]; }) : null;
    var n = 0, garde = 0;
    var cur = new Date(ev.debut.getTime());
    while (garde++ < 5000) {
        if (jusqu && cur > jusqu) break;
        if (cur >= fin) break;
        if (freq === "WEEKLY" && jours) {
            // Chaque jour de la semaine demandé, dans la semaine de « cur »
            var lundi = new Date(cur.getTime()); lundi.setDate(cur.getDate() - ((cur.getDay() + 6) % 7));
            for (var k = 0; k < 7; k++) {
                var d = new Date(lundi.getTime()); d.setDate(lundi.getDate() + k);
                if (jours.indexOf(d.getDay()) < 0 || d < ev.debut) continue;
                if (jusqu && d > jusqu) break;
                if (compte >= 0 && n >= compte) break;
                n++; ajouter(d);
            }
            if (compte >= 0 && n >= compte) break;
            cur.setDate(cur.getDate() + 7 * pas);
            continue;
        }
        if (compte >= 0 && n >= compte) break;
        n++; ajouter(new Date(cur.getTime()));
        if (freq === "DAILY") cur.setDate(cur.getDate() + pas);
        else if (freq === "WEEKLY") cur.setDate(cur.getDate() + 7 * pas);
        else if (freq === "MONTHLY") cur.setMonth(cur.getMonth() + pas);
        else if (freq === "YEARLY") cur.setFullYear(cur.getFullYear() + pas);
        else break;
    }
    return res;
}

// Événements des `jours` prochains jours, triés, `max` au plus
function aVenir(texte, maintenant, jours, max) {
    var debut = new Date(maintenant.getFullYear(), maintenant.getMonth(), maintenant.getDate());
    var fin = new Date(debut.getTime()); fin.setDate(fin.getDate() + jours);
    var tous = [];
    evenements(texte).forEach(function (e) { tous = tous.concat(occurrences(e, maintenant, fin)); });
    tous.sort(function (a, b) { return a.debut - b.debut; });
    return tous.slice(0, max);
}
