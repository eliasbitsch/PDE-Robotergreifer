FeatureScript 3070;
import(path : "onshape/std/geometry.fs", version : "3070.0");

/**
 * Greiferzange fuer Bauteil B - PDE MRE WS26, Gruppe 10.
 *
 * Kragarm mit Anschraubkopf, Backentasche und Ausrundung an der Einspannung.
 * Die Vorgabewerte entsprechen cad/params.py der Python-Konstruktion.
 */
annotation { "Feature Type Name" : "Greiferzange" }
export const greiferzange = defineFeature(function(context is Context, id is Id, definition is map)
    precondition
    {
        annotation { "Name" : "Kraglaenge" }
        isLength(definition.laenge, { (millimeter) : [20, 120, 400] } as LengthBoundSpec);

        annotation { "Name" : "Breite" }
        isLength(definition.breite, { (millimeter) : [8, 25, 120] } as LengthBoundSpec);

        annotation { "Name" : "Dicke" }
        isLength(definition.dicke, { (millimeter) : [3, 8, 60] } as LengthBoundSpec);

        annotation { "Name" : "Ausrundung Einspannung" }
        isLength(definition.ausrundung, { (millimeter) : [0.5, 3, 20] } as LengthBoundSpec);

        annotation { "Name" : "Kopfhoehe" }
        isLength(definition.kopfhoehe, { (millimeter) : [4, 10, 40] } as LengthBoundSpec);

        annotation { "Name" : "Backentasche Laenge" }
        isLength(definition.backeLaenge, { (millimeter) : [10, 60, 300] } as LengthBoundSpec);

        annotation { "Name" : "Backentasche Tiefe" }
        isLength(definition.backeTiefe, { (millimeter) : [0.5, 1.5, 10] } as LengthBoundSpec);

        annotation { "Name" : "Schraubenlochkreis" }
        isLength(definition.lochAbstand, { (millimeter) : [4, 18, 80] } as LengthBoundSpec);

        annotation { "Name" : "Durchgangsbohrung" }
        isLength(definition.lochDurchmesser, { (millimeter) : [2, 6.6, 20] } as LengthBoundSpec);
    }
    {
        const L = definition.laenge;
        const B = definition.breite;
        const H = definition.dicke;
        const HK = definition.kopfhoehe;
        const kopfBreite = H + 12 * millimeter;

        // Anschraubkopf: z = 0 .. HK
        fCuboid(context, id + "kopf", {
                "corner1" : vector(-kopfBreite / 2, -B / 2, 0 * millimeter),
                "corner2" : vector(kopfBreite / 2, B / 2, HK)
        });

        // Kragarm: z = HK .. HK + L
        fCuboid(context, id + "arm", {
                "corner1" : vector(-H / 2, -B / 2, HK),
                "corner2" : vector(H / 2, B / 2, HK + L)
        });

        // ACHTUNG: opBoolean erzeugt KEINEN neuen Koerper unter der
        // Operations-ID. Der vereinigte Koerper behaelt die ID seines ersten
        // Bestandteils. qCreatedBy(id + "vereinen", ...) laeuft deshalb ins
        // Leere -> CANNOT_RESOLVE_ENTITIES. Alle weiteren Operationen muessen
        // sich auf den Kopf-Koerper beziehen.
        opBoolean(context, id + "vereinen", {
                "tools" : qUnion([qCreatedBy(id + "kopf", EntityType.BODY),
                            qCreatedBy(id + "arm", EntityType.BODY)]),
                "operationType" : BooleanOperationType.UNION
        });

        const koerper = qCreatedBy(id + "kopf", EntityType.BODY);

        // Backentasche an der Innenseite (-X) am freien Ende
        const t = definition.backeTiefe;
        const bl = definition.backeLaenge;
        fCuboid(context, id + "tasche", {
                "corner1" : vector(-H / 2 - 1 * millimeter, -(B - 10 * millimeter) / 2,
                        HK + L - bl),
                "corner2" : vector(-H / 2 + t, (B - 10 * millimeter) / 2, HK + L)
        });

        opBoolean(context, id + "tascheAbziehen", {
                "tools" : qCreatedBy(id + "tasche", EntityType.BODY),
                "targets" : koerper,
                "operationType" : BooleanOperationType.SUBTRACTION
        });

        // Zwei Durchgangsbohrungen im Kopf
        const r = definition.lochDurchmesser / 2;
        const a = definition.lochAbstand / 2;
        for (var s in [-1, 1])
        {
            fCylinder(context, id + ("loch" ~ s), {
                    "topCenter" : vector(0 * millimeter, s * a, HK + 1 * millimeter),
                    "bottomCenter" : vector(0 * millimeter, s * a, -1 * millimeter),
                    "radius" : r
            });
        }

        opBoolean(context, id + "loecherAbziehen", {
                "tools" : qUnion([qCreatedBy(id + "loch-1", EntityType.BODY),
                            qCreatedBy(id + "loch1", EntityType.BODY)]),
                "targets" : koerper,
                "operationType" : BooleanOperationType.SUBTRACTION
        });

        // Ausrundung am Uebergang Kopf -> Arm. Massgeblich fuer die Kerbwirkung:
        // die FEM weist dort das Spannungsmaximum aus.
        const kerben = qCoincidesWithPlane(
                    qOwnedByBody(koerper, EntityType.EDGE),
                    plane(vector(0 * millimeter, 0 * millimeter, HK), vector(0, 0, 1)));

        opFillet(context, id + "ausrundung", {
                "entities" : kerben,
                "radius" : definition.ausrundung
        });
    });
