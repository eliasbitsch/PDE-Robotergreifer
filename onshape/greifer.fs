FeatureScript 3070;
import(path : "onshape/std/geometry.fs", version : "3070.0");

/**
 * Robotergreifer fuer Bauteil B - PDE MRE WS26, Gruppe 10.
 * Bitsch Elias, Ovdiienko Viktoriia.
 *
 * Zahnstange-Ritzel mit Servoantrieb. Erzeugt alle Bauteile der Baugruppe
 * als getrennte Koerper in einem Part Studio.
 *
 * Aufbau in z (z = 0 an der Roboter-Flanschflaeche, +z zum Bauteil):
 *     0 ..  10   Adapterplatte (ISO 9409-1-50-4-M6)
 *    10 ..  24   Schnellwechsler Roboterseite
 *    24 ..  40   Schnellwechsler Greiferseite
 *    40 ..  95   Gehaeuse mit Mechanik
 *    95 .. 105   Backenflansch der Zahnstangen
 *   105 .. 115   Anschraubkopf der Zangen
 *   115 .. 235   Greiferzangen
 *
 * Die Zahnstangen liegen UEBEREINANDER, damit die Ritzelachse waagerecht
 * steht und der Motor seitlich angeflanscht werden kann. Laege die Achse
 * senkrecht, wuerde der Motor in den Roboterflansch oder ins Bauteil ragen.
 *
 * Die Verzahnung ist als Trapezprofil ausgefuehrt (Ersatzgeometrie); der
 * Tragfaehigkeitsnachweis erfolgt analytisch, nicht ueber die Modellgeometrie.
 */

annotation { "Feature Type Name" : "Greifer Bauteil B" }
export const greifer = defineFeature(function(context is Context, id is Id, definition is map)
    precondition
    {
        annotation { "Group Name" : "Bauteil", "Collapsed By Default" : false }
        {
            annotation { "Name" : "Greifabstand" }
            isLength(definition.greifAbstand, { (millimeter) : [20, 70, 300] } as LengthBoundSpec);

            annotation { "Name" : "Backenhub je Seite" }
            isLength(definition.hub, { (millimeter) : [2, 12, 50] } as LengthBoundSpec);
        }

        annotation { "Group Name" : "Verzahnung", "Collapsed By Default" : false }
        {
            annotation { "Name" : "Modul" }
            isLength(definition.modul, { (millimeter) : [0.3, 1, 4] } as LengthBoundSpec);

            annotation { "Name" : "Zaehnezahl Ritzel" }
            isInteger(definition.zRitzel, { (unitless) : [8, 20, 60] } as IntegerBoundSpec);

            annotation { "Name" : "Zahnbreite" }
            isLength(definition.zahnBreite, { (millimeter) : [3, 8, 40] } as LengthBoundSpec);
        }

        annotation { "Group Name" : "Zange", "Collapsed By Default" : true }
        {
            annotation { "Name" : "Kraglaenge" }
            isLength(definition.zangeL, { (millimeter) : [20, 120, 400] } as LengthBoundSpec);

            annotation { "Name" : "Breite" }
            isLength(definition.zangeB, { (millimeter) : [8, 25, 120] } as LengthBoundSpec);

            annotation { "Name" : "Dicke" }
            isLength(definition.zangeH, { (millimeter) : [3, 8, 60] } as LengthBoundSpec);

            annotation { "Name" : "Ausrundung Einspannung" }
            isLength(definition.ausrundung, { (millimeter) : [0.5, 3, 20] } as LengthBoundSpec);

            annotation { "Name" : "Backentasche Laenge" }
            isLength(definition.backeL, { (millimeter) : [10, 60, 300] } as LengthBoundSpec);
        }

        annotation { "Group Name" : "Gehaeuse", "Collapsed By Default" : true }
        {
            annotation { "Name" : "Laenge" }
            isLength(definition.gehX, { (millimeter) : [60, 124, 400] } as LengthBoundSpec);

            annotation { "Name" : "Breite" }
            isLength(definition.gehY, { (millimeter) : [30, 60, 200] } as LengthBoundSpec);

            annotation { "Name" : "Hoehe" }
            isLength(definition.gehZ, { (millimeter) : [30, 55, 200] } as LengthBoundSpec);
        }

        annotation { "Name" : "Gehaeuse aufschneiden (Darstellung)" }
        definition.schnitt is boolean;

        annotation { "Group Name" : "Antrieb", "Collapsed By Default" : true }
        {
            annotation { "Name" : "Motorflansch (NEMA)" }
            isLength(definition.motFlansch, { (millimeter) : [20, 42, 90] } as LengthBoundSpec);

            annotation { "Name" : "Baulaenge Motoreinheit" }
            isLength(definition.motL, { (millimeter) : [40, 108, 300] } as LengthBoundSpec);
        }
    }
    {
        // ---------------------------------------------------------- Groessen
        const mm = millimeter;
        const gA = definition.greifAbstand;
        const hub = definition.hub;
        const m = definition.modul;
        const zR = definition.zRitzel;
        const bZ = definition.zahnBreite;
        const ZL = definition.zangeL;
        const ZB = definition.zangeB;
        const ZH = definition.zangeH;
        const gehX = definition.gehX;
        const gehY = definition.gehY;
        const gehZ = definition.gehZ;

        const rTeil = m * zR / 2;
        const hKopf = m;
        const hFuss = 1.25 * m;
        const hZahn = hKopf + hFuss;
        const ueberlapp = 0.6 * mm;      // Zaehne greifen in den Grundkoerper

        const zKoerper = 40 * mm;
        const zUnten = zKoerper + gehZ;
        const zKopf = zUnten + 10 * mm;          // Anschraubkopf der Zange
        const zZange = zKopf + 10 * mm;
        const zAchse = zKoerper + gehZ / 2;      // Ritzelachse, waagerecht in y

        const xZange = gA / 2 + 8 * mm + ZH / 2;
        const schlH = 14 * mm;
        const schlB = 16 * mm;
        const dWelle = 8 * mm;

        const zTeilO = zAchse - rTeil;
        const zTeilU = zAchse + rTeil;
        const zRackO = zTeilO - hFuss - schlH;
        const zRackU = zTeilU + hFuss;

        // ---------------------------------------------------- Roboterflansch
        // ISO 9409-1-50-4-M6: Lochkreis 50, Zentrierung 31,5, 4x M6
        const dFlansch = 63 * mm;
        const rLoch = 25 * mm;
        fCylinder(context, id + "adapter", {
                "topCenter" : vector(0 * mm, 0 * mm, 10 * mm),
                "bottomCenter" : vector(0 * mm, 0 * mm, 0 * mm),
                "radius" : dFlansch / 2
        });
        for (var i = 0; i < 4; i += 1)
        {
            const a = (45 + 90 * i) * degree;
            fCylinder(context, id + ("flBohr" ~ i), {
                    "topCenter" : vector(rLoch * cos(a), rLoch * sin(a), 11 * mm),
                    "bottomCenter" : vector(rLoch * cos(a), rLoch * sin(a), -1 * mm),
                    "radius" : 3.3 * mm
            });
        }
        var flBohr = [];
        for (var i = 0; i < 4; i += 1)
            flBohr = append(flBohr, qCreatedBy(id + ("flBohr" ~ i), EntityType.BODY));
        opBoolean(context, id + "adapterBohren", {
                "tools" : qUnion(flBohr),
                "targets" : qCreatedBy(id + "adapter", EntityType.BODY),
                "operationType" : BooleanOperationType.SUBTRACTION
        });

        // -------------------------------------------- Schnellwechselsystem
        fCylinder(context, id + "wechslerR", {
                "topCenter" : vector(0 * mm, 0 * mm, 24 * mm),
                "bottomCenter" : vector(0 * mm, 0 * mm, 10 * mm),
                "radius" : 29 * mm
        });
        fCylinder(context, id + "wechslerG", {
                "topCenter" : vector(0 * mm, 0 * mm, 40 * mm),
                "bottomCenter" : vector(0 * mm, 0 * mm, 24 * mm),
                "radius" : 29 * mm
        });

        // ------------------------------------------------------- Gehaeuse
        // GESTALTUNG: ein geschlossenes Volumen statt Anbauteile. Der Motor
        // sitzt INNEN, gegenueber liegt der Raum fuer den Motortreiber. Das
        // macht den Koerper symmetrisch und zentriert den Schwerpunkt ueber
        // der Flanschachse - ein seitlich auskragender Motor erzeugt sonst
        // ein Kippmoment am Handgelenk.
        // Grundkoerper: schlank, nur so breit wie die Mechanik braucht.
        fCuboid(context, id + "geh", {
                "corner1" : vector(-gehX / 2, -gehY / 2, zKoerper),
                "corner2" : vector(gehX / 2, gehY / 2, zUnten)
        });
        const gehKoerper = qCreatedBy(id + "geh", EntityType.BODY);

        // Fuehrungstaschen fuer beide Zahnstangen
        fCuboid(context, id + "tascheO", {
                "corner1" : vector(-30 * mm, -schlB / 2 - 0.2 * mm, zRackO),
                "corner2" : vector(gehX / 2 + 2 * mm, schlB / 2 + 0.2 * mm, zTeilO + hKopf)
        });
        fCuboid(context, id + "tascheU", {
                "corner1" : vector(-gehX / 2 - 2 * mm, -schlB / 2 - 0.2 * mm, zTeilU - hKopf),
                "corner2" : vector(30 * mm, schlB / 2 + 0.2 * mm, zRackU + schlH)
        });
        // Freiraum fuer die Stege zu den Backenflanschen
        for (var s in [-1, 1])
        {
            const xm = s * xZange;
            fCuboid(context, id + ("stegFrei" ~ s), {
                    "corner1" : vector(xm - 15 * mm - hub, -schlB / 2 - 0.2 * mm, zRackO + schlH),
                    "corner2" : vector(xm + 15 * mm + hub, schlB / 2 + 0.2 * mm, zUnten + 1 * mm)
            });
        }
        // Ritzelfreiraum und Lagerbohrung, Achse in y
        fCylinder(context, id + "ritzelFrei", {
                "topCenter" : vector(0 * mm, bZ / 2 + 1 * mm, zAchse),
                "bottomCenter" : vector(0 * mm, -bZ / 2 - 1 * mm, zAchse),
                "radius" : rTeil + hKopf + 1 * mm
        });
        fCylinder(context, id + "wellenBohr", {
                "topCenter" : vector(0 * mm, gehY, zAchse),
                "bottomCenter" : vector(0 * mm, -gehY, zAchse),
                "radius" : dWelle / 2 + 0.1 * mm
        });
        // Anschraubbild zum Schnellwechsler
        for (var i = 0; i < 4; i += 1)
        {
            const a = (45 + 90 * i) * degree;
            fCylinder(context, id + ("gehBohr" ~ i), {
                    "topCenter" : vector(rLoch * cos(a), rLoch * sin(a), zKoerper + 12 * mm),
                    "bottomCenter" : vector(rLoch * cos(a), rLoch * sin(a), zKoerper - 1 * mm),
                    "radius" : 2.5 * mm
            });
        }

        var gehWeg = [qCreatedBy(id + "tascheO", EntityType.BODY),
                      qCreatedBy(id + "tascheU", EntityType.BODY),
                      qCreatedBy(id + "ritzelFrei", EntityType.BODY),
                      qCreatedBy(id + "wellenBohr", EntityType.BODY),
                      ];
        for (var s in [-1, 1])
            gehWeg = append(gehWeg, qCreatedBy(id + ("stegFrei" ~ s), EntityType.BODY));
        for (var i = 0; i < 4; i += 1)
            gehWeg = append(gehWeg, qCreatedBy(id + ("gehBohr" ~ i), EntityType.BODY));

        opBoolean(context, id + "gehAusschneiden", {
                "tools" : qUnion(gehWeg),
                "targets" : gehKoerper,
                "operationType" : BooleanOperationType.SUBTRACTION
        });

        // --------------------------------------------------------- Ritzel
        fCylinder(context, id + "ritzelNabe", {
                "topCenter" : vector(0 * mm, bZ / 2, zAchse),
                "bottomCenter" : vector(0 * mm, -bZ / 2, zAchse),
                "radius" : rTeil - hFuss
        });
        const teilung = PI * m;
        const zahnDicke = teilung / 2 - 0.12 * mm;     // Flankenspiel
        var zaehne = [];
        for (var i = 0; i < zR; i += 1)
        {
            // fCuboid erzeugt AUSSCHLIESSLICH achsparallele Quader. Der Zahn
            // wird deshalb oben am Teilkreis achsparallel gebaut und
            // anschliessend um die Ritzelachse gedreht.
            const r = rTeil + (hKopf - hFuss) / 2 - ueberlapp / 2;
            fCuboid(context, id + ("rZahn" ~ i), {
                    "corner1" : vector(-zahnDicke / 2, -bZ / 2,
                                zAchse + r - (hZahn + ueberlapp) / 2),
                    "corner2" : vector(zahnDicke / 2, bZ / 2,
                                zAchse + r + (hZahn + ueberlapp) / 2)
            });
            opTransform(context, id + ("rZahnDreh" ~ i), {
                    "bodies" : qCreatedBy(id + ("rZahn" ~ i), EntityType.BODY),
                    "transform" : rotationAround(
                                line(vector(0 * mm, 0 * mm, zAchse), vector(0, 1, 0)),
                                360 * i / zR * degree)
            });
            zaehne = append(zaehne, qCreatedBy(id + ("rZahn" ~ i), EntityType.BODY));
        }

        opBoolean(context, id + "ritzelVereinen", {
                "tools" : qUnion(concatenateArrays([
                            [qCreatedBy(id + "ritzelNabe", EntityType.BODY)], zaehne])),
                "operationType" : BooleanOperationType.UNION
        });
        fCylinder(context, id + "wellenSitz", {
                "topCenter" : vector(0 * mm, bZ / 2 + 1 * mm, zAchse),
                "bottomCenter" : vector(0 * mm, -bZ / 2 - 1 * mm, zAchse),
                "radius" : dWelle / 2
        });
        opBoolean(context, id + "ritzelBohren", {
                "tools" : qCreatedBy(id + "wellenSitz", EntityType.BODY),
                "targets" : qCreatedBy(id + "ritzelNabe", EntityType.BODY),
                "operationType" : BooleanOperationType.SUBTRACTION
        });

        // --------------------------------------------------- Ritzelwelle
        fCylinder(context, id + "welle", {
                "topCenter" : vector(0 * mm, gehY / 2, zAchse),
                "bottomCenter" : vector(0 * mm, -gehY / 2, zAchse),
                "radius" : dWelle / 2
        });

        // ----------------------------------------------------- Zahnstangen
        // s = +1: obere Zahnstange, Zaehne nach unten, Backe bei +x
        // s = -1: untere Zahnstange, Zaehne nach oben,  Backe bei -x
        for (var s in [-1, 1])
        {
            const oben = s > 0;
            const zK = oben ? zRackO : zRackU;
            const zZahn = oben ? zTeilO - hFuss - ueberlapp : zTeilU - hKopf;
            const xv = oben ? -30 * mm : -50 * mm;
            const xb = oben ? 50 * mm : 30 * mm;

            fCuboid(context, id + ("rack" ~ s), {
                    "corner1" : vector(xv, -schlB / 2, zK),
                    "corner2" : vector(xb, schlB / 2, zK + schlH)
            });
            var rackTeile = [];
            var k = 0;
            for (var x = -22 * mm; x <= 22 * mm; x += teilung)
            {
                if (x < xv + 2 * mm || x > xb - 2 * mm)
                    continue;
                fCuboid(context, id + ("sZahn" ~ s ~ "_" ~ k), {
                        "corner1" : vector(x - zahnDicke / 2, -bZ / 2, zZahn),
                        "corner2" : vector(x + zahnDicke / 2, bZ / 2, zZahn + hZahn + ueberlapp)
                });
                rackTeile = append(rackTeile,
                        qCreatedBy(id + ("sZahn" ~ s ~ "_" ~ k), EntityType.BODY));
                k += 1;
            }
            // Steg nach unten und Backenflansch
            const xm = s * xZange;
            fCuboid(context, id + ("steg" ~ s), {
                    "corner1" : vector(xm - 13 * mm, -schlB / 2, zK + schlH),
                    "corner2" : vector(xm + 13 * mm, schlB / 2, zUnten)
            });
            fCuboid(context, id + ("bFlansch" ~ s), {
                    "corner1" : vector(xm - 15 * mm, -(schlB + 10 * mm) / 2, zUnten),
                    "corner2" : vector(xm + 15 * mm, (schlB + 10 * mm) / 2, zUnten + 10 * mm)
            });
            rackTeile = append(rackTeile, qCreatedBy(id + ("steg" ~ s), EntityType.BODY));
            rackTeile = append(rackTeile, qCreatedBy(id + ("bFlansch" ~ s), EntityType.BODY));
            opBoolean(context, id + ("rackVereinen" ~ s), {
                    "tools" : qUnion(concatenateArrays([
                                [qCreatedBy(id + ("rack" ~ s), EntityType.BODY)], rackTeile])),
                    "operationType" : BooleanOperationType.UNION
            });
        }

        // ------------------------------------------------------- Zangen
        for (var s in [-1, 1])
        {
            const x = s * xZange;
            fCuboid(context, id + ("zKopf" ~ s), {
                    "corner1" : vector(x - (ZH + 12 * mm) / 2, -ZB / 2, zKopf),
                    "corner2" : vector(x + (ZH + 12 * mm) / 2, ZB / 2, zZange)
            });
            fCuboid(context, id + ("zArm" ~ s), {
                    "corner1" : vector(x - ZH / 2, -ZB / 2, zZange),
                    "corner2" : vector(x + ZH / 2, ZB / 2, zZange + ZL)
            });
            opBoolean(context, id + ("zVereinen" ~ s), {
                    "tools" : qUnion([qCreatedBy(id + ("zKopf" ~ s), EntityType.BODY),
                                qCreatedBy(id + ("zArm" ~ s), EntityType.BODY)]),
                    "operationType" : BooleanOperationType.UNION
            });
            const zKoerperQ = qCreatedBy(id + ("zKopf" ~ s), EntityType.BODY);

            // Backentasche am freien Ende
            const xi = s * (gA / 2 + 8 * mm);
            fCuboid(context, id + ("zTasche" ~ s), {
                    "corner1" : vector(xi - 1.5 * mm, -(ZB - 10 * mm) / 2,
                                zZange + ZL - definition.backeL),
                    "corner2" : vector(xi + 1.5 * mm, (ZB - 10 * mm) / 2, zZange + ZL)
            });
            // zwei Durchgangsbohrungen im Kopf
            var zBohr = [qCreatedBy(id + ("zTasche" ~ s), EntityType.BODY)];
            for (var j in [-1, 1])
            {
                fCylinder(context, id + ("zBohr" ~ s ~ "_" ~ j), {
                        "topCenter" : vector(x, j * 9 * mm, zZange + 1 * mm),
                        "bottomCenter" : vector(x, j * 9 * mm, zKopf - 1 * mm),
                        "radius" : 3.3 * mm
                });
                zBohr = append(zBohr, qCreatedBy(id + ("zBohr" ~ s ~ "_" ~ j), EntityType.BODY));
            }
            opBoolean(context, id + ("zAbziehen" ~ s), {
                    "tools" : qUnion(zBohr),
                    "targets" : zKoerperQ,
                    "operationType" : BooleanOperationType.SUBTRACTION
            });
            // Ausrundung am Uebergang Kopf -> Arm (Kerbwirkung, FEM-Maximum)
            opFillet(context, id + ("zFillet" ~ s), {
                    "entities" : qCoincidesWithPlane(
                                qOwnedByBody(zKoerperQ, EntityType.EDGE),
                                plane(vector(0 * mm, 0 * mm, zZange), vector(0, 0, 1))),
                    "radius" : definition.ausrundung
            });

            // Weichbacke
            fCuboid(context, id + ("backe" ~ s), {
                    "corner1" : vector(s * (gA / 2), -(ZB - 10 * mm) / 2,
                                zZange + ZL - definition.backeL),
                    "corner2" : vector(xi + 1.5 * mm, (ZB - 10 * mm) / 2, zZange + ZL)
            });
        }

        // ------------------------------------------- Schnittdarstellung
        // Schneidet die vordere Haelfte des Gehaeuses weg, damit Ritzel und
        // Zahnstangen sichtbar werden. Reine Darstellungsoption fuer den
        // Bericht - fuer Fertigung und Stueckliste ausgeschaltet lassen.
        if (definition.schnitt)
        {
            fCuboid(context, id + "schnittWerkzeug", {
                    "corner1" : vector(-gehX, -gehY, zKoerper - 1 * mm),
                    "corner2" : vector(gehX, 0 * mm, zUnten + 1 * mm)
            });
            opBoolean(context, id + "schneiden", {
                    "tools" : qCreatedBy(id + "schnittWerkzeug", EntityType.BODY),
                    "targets" : gehKoerper,
                    "operationType" : BooleanOperationType.SUBTRACTION
            });
        }

        // ------------------------------------------------- Benennung
        // Ohne Namen heissen die Koerper "Part 1..13" und die Stueckliste
        // waere wertlos. Die Nummern folgen der Stueckliste im Bericht.
        const benennung = [
            ["adapter",   "Pos1 Adapterplatte"],
            ["wechslerR", "Pos2 Schnellwechsler Roboterseite"],
            ["wechslerG", "Pos3 Schnellwechsler Greiferseite"],
            ["geh",       "Pos4 Greifergehaeuse"],
            ["ritzelNabe", "Pos5 Ritzel m" ~ (m / millimeter) ~ " z" ~ zR],
            ["welle",     "Pos6 Ritzelwelle"],
            ["rack1",     "Pos7 Zahnstange oben"],
            ["rack-1",    "Pos7 Zahnstange unten"],
            ["zKopf1",    "Pos9 Greiferzange links"],
            ["zKopf-1",   "Pos9 Greiferzange rechts"],
            ["backe1",    "Pos10 Weichbacke links"],
            ["backe-1",   "Pos10 Weichbacke rechts"]
        ];
        for (var b in benennung)
        {
            setProperty(context, {
                    "entities" : qCreatedBy(id + b[0], EntityType.BODY),
                    "propertyType" : PropertyType.NAME,
                    "value" : b[1]
            });
        }

        // ------------------------------------------------- Motoreinheit
        const mf = definition.motFlansch;
        const y0 = gehY / 2;
        fCylinder(context, id + "getriebe", {
                "topCenter" : vector(0 * mm, y0 + 40 * mm, zAchse),
                "bottomCenter" : vector(0 * mm, y0, zAchse),
                "radius" : 18 * mm
        });
        fCuboid(context, id + "motor", {
                "corner1" : vector(-mf / 2, y0 + 40 * mm, zAchse - mf / 2),
                "corner2" : vector(mf / 2, y0 + 80 * mm, zAchse + mf / 2)
        });
        fCylinder(context, id + "bremse", {
                "topCenter" : vector(0 * mm, y0 + definition.motL, zAchse),
                "bottomCenter" : vector(0 * mm, y0 + 80 * mm, zAchse),
                "radius" : 19 * mm
        });
        opBoolean(context, id + "motorVereinen", {
                "tools" : qUnion([qCreatedBy(id + "getriebe", EntityType.BODY),
                            qCreatedBy(id + "motor", EntityType.BODY),
                            qCreatedBy(id + "bremse", EntityType.BODY)]),
                "operationType" : BooleanOperationType.UNION
        });
            setProperty(context, {
                "entities" : qCreatedBy(id + "getriebe", EntityType.BODY),
                "propertyType" : PropertyType.NAME,
                "value" : "Pos8 Servomotor mit Getriebe und Bremse"
        });
    });
