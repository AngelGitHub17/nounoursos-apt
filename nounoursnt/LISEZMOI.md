# NounoursNT

Système d'exploitation NT de NounoursCorp, **basé sur les sources de [LiberNT](https://github.com/LiberNT/LiberNT)**
(lui-même issu de ReactOS), aux couleurs de NounoursOS.

- `rebaptiser.py` : appliqué à une copie des sources de LiberNT, il remplace le nom et le logo de LiberNT
  par l'identité NounoursOS, comme le demande [la politique de marque de LiberNT](https://github.com/LiberNT/LiberNT/blob/master/TRADEMARK.md) :
  une version modifiée ne doit ni s'appeler LiberNT, ni embarquer son logo. L'attribution et les mentions
  de copyright du code restent intactes.
- Construction : workflow GitHub Actions **« Construire NounoursNT »** (onglet Actions). Il compile la
  version AMD64, la démarre dans QEMU pour une capture d'écran, puis publie une Release `nounoursnt-…`.

NounoursNT n'est pas un produit du projet LiberNT. Licence : GNU GPL 3.0 (le code repris garde sa licence
d'origine). C'est un aperçu de développement : à essayer dans une machine virtuelle.
