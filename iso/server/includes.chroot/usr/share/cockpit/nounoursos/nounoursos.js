/* Tableau de bord NounoursOS Server : rôles en un clic (via /usr/libexec/nounoursos/nounoursos-roles). */
"use strict";
const ROLES = "/usr/libexec/nounoursos/nounoursos-roles";
const INFOS = {
    web: { nom: "Site web", lettre: "W", couleur: "#2F6FDB",
           desc: "Apache, PHP et MariaDB (MySQL) : hébergez vos sites PHP.",
           lien: (ip) => `http://${ip}/` },
    jellyfin: { nom: "Jellyfin", lettre: "J", couleur: "#7B4BD6",
                desc: "Vos films, séries et musique en streaming sur tous vos appareils.",
                lien: (ip) => `http://${ip}:8096/` },
    minecraft: { nom: "Minecraft (Paper)", lettre: "M", couleur: "#3F8E3C",
                 desc: "Un serveur Paper prêt à jouer, sauvegardes comprises.",
                 lien: null },
};
let admin = false;
let occupe = false;
const $ = (id) => document.getElementById(id);

function journal(texte, remplacer) {
    const j = $("journal");
    j.textContent = remplacer ? texte : j.textContent + texte;
    j.scrollTop = j.scrollHeight;
}

function lancer(args, titre) {
    if (occupe) return Promise.reject(new Error("occupé"));
    occupe = true;
    afficher(dernierEtat);
    journal(`› ${titre}\n`, true);
    return cockpit.spawn([ROLES, ...args], { superuser: "require", err: "out" })
        .stream((d) => journal(d))
        .then(() => journal("\n✓ Terminé.\n"))
        .catch((e) => journal(`\n✗ Échec : ${e.message || e}\n`))
        .finally(() => { occupe = false; rafraichir(); });
}

function bouton(texte, classe, action) {
    const b = document.createElement("button");
    b.textContent = texte;
    if (classe) b.className = classe;
    b.disabled = occupe || !admin;
    b.addEventListener("click", action);
    return b;
}

let dernierEtat = null;
function afficher(etat) {
    if (!etat) return;
    dernierEtat = etat;
    const zone = $("roles");
    zone.textContent = "";
    for (const [cle, info] of Object.entries(INFOS)) {
        const r = etat[cle] || {};
        const carte = document.createElement("article");
        carte.className = "carte role";
        carte.innerHTML = `<div class="titre"><div class="pastille"></div><h3></h3></div>
            <p class="desc"></p><div class="etat"></div><div class="actions"></div>`;
        carte.querySelector(".pastille").textContent = info.lettre;
        carte.querySelector(".pastille").style.background = info.couleur;
        carte.querySelector("h3").textContent = info.nom;
        carte.querySelector(".desc").textContent = info.desc;
        const e = carte.querySelector(".etat");
        if (!r.installe) {
            e.textContent = "Non installé";
        } else {
            e.innerHTML = r.actif ? '<b class="ok">● En marche</b>' : '<b class="non">● Arrêté</b>';
            let plus = ` · port ${r.port}`;
            if (cle === "minecraft") {
                if (r.version) plus += ` · Paper ${r.version}`;
                if (r.joueurs) plus += ` · ${r.joueurs} joueurs`;
                plus += ` · adresse ${etat.ip}`;
            }
            e.append(plus);
        }
        const a = carte.querySelector(".actions");
        if (!r.installe) {
            a.append(bouton("Installer", "principal", () => {
                if (cle === "minecraft") return ouvrirMinecraft();
                lancer(["installer", cle], `Installation : ${info.nom}`);
            }));
        } else {
            if (r.actif) a.append(bouton("Arrêter", "", () => lancer(["arreter", cle], `Arrêt : ${info.nom}`)));
            else a.append(bouton("Démarrer", "principal", () => lancer(["demarrer", cle], `Démarrage : ${info.nom}`)));
            if (info.lien && r.actif) {
                const l = document.createElement("a");
                l.href = info.lien(etat.ip); l.target = "_blank"; l.rel = "noopener";
                l.textContent = "Ouvrir ↗";
                l.style.alignSelf = "center";
                a.append(l);
            }
            if (cle === "minecraft")
                a.append(bouton("Sauvegarder le monde", "", () => lancer(["minecraft-sauvegarder"], "Sauvegarde du monde")));
            a.append(bouton("Retirer", "", () => {
                if (confirm(`Arrêter et désactiver ${info.nom} ? Les données sont conservées.`))
                    lancer(["retirer", cle], `Retrait : ${info.nom}`);
            }));
        }
        zone.append(carte);
    }
}

function rafraichir() {
    cockpit.spawn([ROLES, "etat"], { superuser: "try" })
        .then((sortie) => afficher(JSON.parse(sortie)))
        .catch((e) => journal(`Impossible de lire l'état : ${e.message || e}\n`, true));
}

function ouvrirMinecraft() {
    $("mc-panneau").hidden = false;
    $("mc-panneau").scrollIntoView({ behavior: "smooth" });
    cockpit.http({ address: "fill.papermc.io", port: 443, tls: {} })
        .get("/v3/projects/paper", null, { "User-Agent": "NounoursOS Server (https://nounourscorp.fr/)" })
        .then((t) => {
            const v = [];
            for (const groupe of Object.values(JSON.parse(t).versions || {}))
                for (const x of groupe) if (/^[\d.]+$/.test(x)) v.push(x);
            v.sort((a, b) => b.split(".").map(Number).reduce((r, n, i) => r || n - (a.split(".").map(Number)[i] || 0), 0));
            $("mc-version").innerHTML = "";
            for (const x of v.slice(0, 30)) $("mc-version").append(new Option(x, x));
        })
        .catch(() => { $("mc-version").innerHTML = '<option value="">La plus récente</option>'; });
}

document.addEventListener("DOMContentLoaded", () => {
    $("mc-cluf").addEventListener("change", (e) => { $("mc-go").disabled = !e.target.checked; });
    $("mc-annuler").addEventListener("click", () => { $("mc-panneau").hidden = true; });
    $("mc-go").addEventListener("click", () => {
        if (!$("mc-cluf").checked) return;
        $("mc-panneau").hidden = true;
        lancer(["installer", "minecraft", $("mc-version").value, $("mc-memoire").value, "cluf-accepte"],
               "Installation du serveur Minecraft");
    });
    const perm = cockpit.permission({ admin: true });
    const majPerm = () => { admin = perm.allowed !== false; $("admin").hidden = admin; afficher(dernierEtat); };
    perm.addEventListener("changed", majPerm);
    majPerm();
    rafraichir();
    setInterval(() => { if (!occupe && !document.hidden) rafraichir(); }, 10000);
});
