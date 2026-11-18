// NounoursOS — « pont » entre Paramètres (Python/PyQt6) et les modules de réglage KDE.
// Permet d'afficher un module KDE (KCM) DANS la fenêtre Paramètres, au lieu d'ouvrir
// une fenêtre « Configuration du système » séparée. Interface C, appelée via ctypes.
#include <KCModule>
#include <KCModuleLoader>
#include <KPluginMetaData>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QWidget>

static const QStringList ESPACES = {
    QStringLiteral("plasma/kcms/systemsettings"),
    QStringLiteral("plasma/kcms/systemsettings_qwidgets"),
    QStringLiteral("plasma/kcms/kinfocenter"),
    QStringLiteral("plasma/kcms"),
};

static KPluginMetaData trouver(const QString &id)
{
    for (const QString &ns : ESPACES) {
        const KPluginMetaData md = KPluginMetaData::findPluginById(ns, id);
        if (md.isValid())
            return md;
    }
    return {};
}

static KCModule *M(void *p) { return static_cast<KCModule *>(p); }

extern "C" {

// Charge le module `id` (ex. "kcm_networkmanagement") ; renvoie un KCModule* ou NULL.
void *nkcm_charger(const char *id, void *parent)
{
    const KPluginMetaData md = trouver(QString::fromUtf8(id));
    if (!md.isValid())
        return nullptr;
    KCModule *m = KCModuleLoader::loadModule(md, static_cast<QWidget *>(parent));
    if (!m)
        return nullptr;
    m->load();
    return m;
}

void *nkcm_widget(void *m) { return M(m)->widget(); }
void nkcm_enregistrer(void *m) { M(m)->save(); }
void nkcm_recharger(void *m) { M(m)->load(); }
void nkcm_par_defaut(void *m) { M(m)->defaults(); }
int nkcm_a_enregistrer(void *m) { return M(m)->needsSave() ? 1 : 0; }
int nkcm_existe(const char *id) { return trouver(QString::fromUtf8(id)).isValid() ? 1 : 0; }

// Tous les modules installés, en JSON : [{id, nom, icone, categorie, description}]
const char *nkcm_liste()
{
    static QByteArray json;
    QJsonArray tab;
    QSet<QString> vus;
    for (const QString &ns : ESPACES) {
        for (const KPluginMetaData &md : KPluginMetaData::findPlugins(ns)) {
            if (vus.contains(md.pluginId()))
                continue;
            vus.insert(md.pluginId());
            QJsonObject o;
            o[QStringLiteral("id")] = md.pluginId();
            o[QStringLiteral("nom")] = md.name();
            o[QStringLiteral("icone")] = md.iconName();
            o[QStringLiteral("description")] = md.description();
            o[QStringLiteral("categorie")] = ns.endsWith(QLatin1String("kinfocenter"))
                ? QStringLiteral("infos")
                : md.value(QStringLiteral("X-KDE-System-Settings-Parent-Category"));
            o[QStringLiteral("cache")] = md.value(QStringLiteral("X-KDE-System-Settings-Hidden")) == QLatin1String("true")
                || md.rawData().value(QStringLiteral("X-KDE-OnlyShowOnQtPlatforms")).isArray();
            tab.append(o);
        }
    }
    json = QJsonDocument(tab).toJson(QJsonDocument::Compact);
    return json.constData();
}
}
