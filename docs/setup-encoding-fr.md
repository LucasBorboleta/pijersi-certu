# Introduction

Ce mémo explique une méthode d’encodage compact des mises en place “aléatoire-miroir” et “aléatoire-totale”.

# Principes

1. Les positions des blancs sont encodées par une chaîne de caractères “b” en base 26 ; c’est-à-dire à l’aide des 26 lettres de l'alphabet latin.
2. Les positions de noirs sont encodées de manière similaire par une chaîne de caractères “n”.
3. Si la mise en place est “aléatoire-totale” alors l’encodage est “b-n” ; c’est-à-dire la chaîne “b”, puis le séparateur “-”, et enfin la chaîne “n”.
4. Si la mise en place est “aléatoire-miroir” alors l’encodage est juste “b” ; car la chaîne est “n” est alors égale à la chaîne “b”.

# Algorithme pour les blancs

1. Les cubes sont numérotés de 0 à 13 dans l’ordre suivant : a1 à a6, puis b1 à b3, puis b4-bas suivi de b4-haut, puis b5 à b7.
2. Chaque cube “$c_i$” est encodé en base 4 : 0 = R = Pierre ; 1 = P = Feuille ; 2 = S = Ciseaux ; 3 = W = Sage.
3. Les 14 cubes définissent un entier $s$ par la formule $s=\sum_{i=0}^{13} c_i 4^i$.
4. Cet entier $s$ est ensuite représenté en base 26 à l'aide des 26 lettres majuscules de "A" à "Z".
5. En base 26, au plus $n=6$ digits sont nécessaires pour représenter l’entier s. En effet : $4^{14} \le 26^n \Leftrightarrow n \le 14*log(4)/log(26)\approx 5.96 \implies n=6$ .
6. L’entier $s$ sera représenté avec exactement 6 digits, le cas échéant des "A" sont insérés à gauche.

# Algorithme pour les noirs

Les positions des noirs sont encodées comme pour les blancs avec les adaptations suivantes :

1. Les cubes sont numérotés de 0 à 13 dans l’ordre suivant : g6 à g1, puis f7 à f5, puis f4-bas suivi de f4-haut, puis f3 à f1.
2. Chaque cube $c_i$ est encodé en base 4 : 0 = r  ; 1 = p ; 2 = s ; 3 = w.
3. La base 26 est représentée à l’aide des lettres minuscules de “a” à “z”.

# Exemples

La mise en place standard est encodée soit comme la mise en place “aléatoire-miroir” de code GRXLL, soit comme mise en place “aléatoire-totale” de code GRXLLS-grxlls.

JEXEDA encode la mise en place “aléatoire-miroir” {'a1': 'S', 'a2': 'P', 'a3': 'P', 'a4': 'W', 'a5': 'S', 'a6': 'R', 'b1': 'R', 'b2': 'W', 'b3': 'P', 'b4': 'R', 'b4t': 'R', 'b5': 'S', 'b6': 'S', 'b7': 'P'}.

AYABEY encode la mise en place “aléatoire-miroir” {'a1': 'R', 'a2': 'P', 'a3': 'S', 'a4': 'S', 'a5': 'R', 'a6': 'W', 'b1': 'P', 'b2': 'P', 'b3': 'W', 'b4': 'P', 'b4t': 'S', 'b5': 'S', 'b6': 'R', 'b7': 'R'}.

AWALIC encode la mise en place “aléatoire-miroir” {'a1': 'S', 'a2': 'W', 'a3': 'W', 'a4': 'R', 'a5': 'P', 'a6': 'P', 'b1': 'R', 'b2': 'S', 'b3': 'P', 'b4': 'S', 'b4t': 'P', 'b5': 'S', 'b6': 'R', 'b7': 'R'}.



