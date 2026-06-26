#include <xc.h>
#include <stdint.h>

// Configuration du microcontrôleur 
#pragma config FEXTOSC = OFF
#pragma config RSTOSC = HFINTOSC_64MHZ
#pragma config CLKOUTEN = OFF
#pragma config CSWEN = ON
#pragma config FCMEN = ON

#pragma config MCLRE = EXTMCLR
#pragma config PWRTE = OFF
#pragma config LPBOREN = OFF
#pragma config BOREN = ON
#pragma config BORV = VBOR_2P45
#pragma config WDTE = OFF
#pragma config WDTCCS = SC

#pragma config LVP = ON
#pragma config DEBUG = OFF
#pragma config XINST = OFF
#pragma config STVREN = ON
#pragma config WRT0 = OFF
#pragma config WRT1 = OFF
#pragma config WRT2 = OFF
#pragma config WRT3 = OFF
#pragma config CP = OFF
#pragma config CPD = OFF

// Fréquence de l'horloge utilisée par les fonctions __delay_ms et __delay_us
#define _XTAL_FREQ 64000000UL

// Constantes principales du programme
#define NOMBRE_BANDES       4u     
#define HAUTEUR_MATRICE     8u     
#define OCTETS_PAR_LED      4u     
#define TAILLE_MATRICE      256u   

// Paramètres pour les mesures analogiques et l'affichage
#define MESURES_MOYENNE     4u     
#define MESURES_CALIBRATION 32u    
#define MARGE_BRUIT         12u    
#define PLAGE_AFFICHAGE     550u   
#define DELAI_BOUCLE_MS     20u    

// Valeurs de luminosité selon la couleur affichée
#define LUMINOSITE_VERTE    24u
#define LUMINOSITE_JAUNE    18u
#define LUMINOSITE_ROUGE    24u

extern void TX_64LEDS(void);

volatile uint8_t LED_MATRIX[TAILLE_MATRICE];
volatile uint8_t *pC = LED_MATRIX;

static const uint8_t CANAL_ADC[NOMBRE_BANDES] = {5u, 4u, 3u, 2u};

static uint16_t niveau_zero[NOMBRE_BANDES];
static uint8_t hauteur_barre[NOMBRE_BANDES];

// Initialise les ports du microcontroleur
static void initialiser_ports(void)
{
    LATA = 0x00u;
    LATB = 0x00u;
    LATC = 0x00u;

    ANSELA = 0x3Cu;
    TRISA = 0xFFu;

    ANSELB = 0x00u;
    TRISB = 0xCFu;

    ANSELC = 0x00u;
    TRISC = 0x00u;

    WPUA = 0xC0u;
}

// Configure le convertisseur analogique numerique
static void initialiser_adc(void)
{
    ADCON0 = 0x00u;
    ADCON1 = 0x00u;
    ADCON2 = 0x00u;
    ADCON3 = 0x00u;

    ADREF = 0x00u;
    ADCLK = 0x1Fu;
    ADACQ = 0x08u;
    ADPCH = 0x00u;

    ADCON0bits.ADFM = 1u;
    ADCON0bits.ADON = 1u;
}

// Lit une valeur sur un canal ADC
static uint16_t lire_adc(uint8_t canal)
{
    ADPCH = canal;
    __delay_us(5);

    ADCON0bits.ADGO = 1u;
    while (ADCON0bits.ADGO != 0u) {
    }

    return ((uint16_t)ADRESH << 8) | ADRESL;
}

// Fait une moyenne de plusieurs mesures ADC
static uint16_t lire_adc_moyenne(uint8_t canal)
{
    uint8_t mesure;
    uint16_t somme = 0u;

    for (mesure = 0u; mesure < MESURES_MOYENNE; mesure++) {
        somme = (uint16_t)(somme + lire_adc(canal));
    }

    return (uint16_t)(somme / MESURES_MOYENNE);
}

// Eteint toutes les LEDs de la matrice
static void eteindre_matrice(void)
{
    uint16_t i;

    for (i = 0u; i < TAILLE_MATRICE; i++) {
        LED_MATRIX[i] = 0u;
    }
}

// Allume une LED avec une couleur donnee
static void allumer_led(uint8_t colonne, uint8_t ligne,
                        uint8_t vert, uint8_t rouge)
{
    uint16_t index;

    index = (uint16_t)(colonne * HAUTEUR_MATRICE + ligne);
    index = (uint16_t)(index * OCTETS_PAR_LED);

    LED_MATRIX[index] = vert;
    LED_MATRIX[index + 1u] = rouge;
    LED_MATRIX[index + 2u] = 0u;
    LED_MATRIX[index + 3u] = 0u;
}

// Dessine les barres de niveau sur la matrice
static void dessiner_matrice(void)
{
    uint8_t bande;
    uint8_t colonne;
    uint8_t ligne;
    uint8_t vert;
    uint8_t rouge;

    eteindre_matrice();

    for (bande = 0u; bande < NOMBRE_BANDES; bande++) {
        for (colonne = 0u; colonne < 2u; colonne++) {
            uint8_t x = (uint8_t)(bande * 2u + colonne);

            for (ligne = 0u; ligne < hauteur_barre[bande]; ligne++) {
                if (ligne < 4u) {
                    vert = LUMINOSITE_VERTE;
                    rouge = 0u;
                }
                else if (ligne < 6u) {
                    vert = LUMINOSITE_JAUNE;
                    rouge = LUMINOSITE_JAUNE;
                }
                else {
                    vert = 0u;
                    rouge = LUMINOSITE_ROUGE;
                }

                allumer_led(x, ligne, vert, rouge);
            }
        }
    }
}

// Convertit une mesure ADC en hauteur de barre
static uint8_t calculer_hauteur(uint16_t mesure, uint16_t zero)
{
    uint16_t valeur;
    uint16_t hauteur;

    if (mesure <= (uint16_t)(zero + MARGE_BRUIT)) {
        return 0u;
    }

    valeur = (uint16_t)(mesure - zero - MARGE_BRUIT);

    if (valeur >= PLAGE_AFFICHAGE) {
        return HAUTEUR_MATRICE;
    }

    hauteur = (uint16_t)(valeur * HAUTEUR_MATRICE);
    hauteur = (uint16_t)(hauteur / PLAGE_AFFICHAGE + 1u);

    return (uint8_t)hauteur;
}

// Transforme une hauteur en masque binaire
static uint8_t hauteur_vers_port(uint8_t hauteur)
{
    if (hauteur == 0u) {
        return 0x00u;
    }

    if (hauteur >= HAUTEUR_MATRICE) {
        return 0xFFu;
    }

    return (uint8_t)((1u << hauteur) - 1u);
}

// Calibre le niveau de repos des bandes
static void calibrer_zero(void)
{
    uint8_t bande;
    uint8_t mesure;
    uint32_t somme;

    // Pendant la calibration on éteint l'affichage
    LATBbits.LATB4 = 0u;
    LATC = 0x00u;

    // Pour chaque bande on mesure le niveau de repos
    for (bande = 0u; bande < NOMBRE_BANDES; bande++) {
        somme = 0u;

        for (mesure = 0u; mesure < MESURES_CALIBRATION; mesure++) {
            somme += lire_adc(CANAL_ADC[bande]);
        }

        // Le zéro est la moyenne des mesures prises au repos
        niveau_zero[bande] =
            (uint16_t)(somme / MESURES_CALIBRATION);
        hauteur_barre[bande] = 0u;
    }

    // On envoie une matrice vide pour bien repartir de zéro
    eteindre_matrice();
    TX_64LEDS();
    __delay_us(100);

    // On réactive ensuite la sortie liée à l'affichage
    LATBbits.LATB4 = 1u;
}

// Met a jour les niveaux affiches
static void mettre_a_jour_niveaux(void)
{
    uint8_t bande;
    uint8_t hauteur_demandee;
    uint8_t hauteur_maximale = 0u;
    uint16_t mesure;

    // On lit les 4 bandes une par une
    for (bande = 0u; bande < NOMBRE_BANDES; bande++) {
        mesure = lire_adc_moyenne(CANAL_ADC[bande]);
        hauteur_demandee =
            calculer_hauteur(mesure, niveau_zero[bande]);

        // Si le niveau monte on l'affiche directement
        if (hauteur_demandee >= hauteur_barre[bande]) {
            hauteur_barre[bande] = hauteur_demandee;
        }
        // Si le niveau descend on baisse petit à petit pour avoir un affichage plus fluide
        else if (hauteur_barre[bande] > 0u) {
            hauteur_barre[bande]--;
        }

        // On garde aussi la hauteur la plus grande pour l'afficher sur le port C
        if (hauteur_barre[bande] > hauteur_maximale) {
            hauteur_maximale = hauteur_barre[bande];
        }
    }

    LATC = hauteur_vers_port(hauteur_maximale);
}

// Lance le programme principal
void main(void)
{
    // Initialisation des entrées/sorties et de l'ADC
    initialiser_ports();
    initialiser_adc();

    // Petit délai au démarrage puis calibration du niveau zéro
    __delay_ms(250);
    calibrer_zero();

    while (1) {
        // Si on appuie sur le bouton connecté à RA7 on refait une calibration
        if (PORTAbits.RA7 == 0u) {
            __delay_ms(30);

            if (PORTAbits.RA7 == 0u) {
                calibrer_zero();

                // On attend que le bouton soit relâché pour éviter de recalibrer en boucle
                while (PORTAbits.RA7 == 0u) {
                }
            }
        }

        // Lecture des niveaux mise à jour de la matrice puis envoi aux LEDs
        mettre_a_jour_niveaux();
        dessiner_matrice();
        TX_64LEDS();

        // Délai pour laisser le temps à la matrice de se mettre à jour correctement
        __delay_us(100);
        __delay_ms(DELAI_BOUCLE_MS);
    }
}