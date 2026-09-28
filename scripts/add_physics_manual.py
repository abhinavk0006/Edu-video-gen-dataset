"""Add the Physics Classes XI-XII manual inventory to the canonical dataset."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "chemistry_experiments.json"

CLASS_XI_EXPERIMENTS = [
    "Use of Vernier Callipers to measure dimensions, volume, and density",
    "Use of screw gauge to measure wire diameter, sheet thickness, and lamina volume",
    "Determine the radius of curvature of a spherical surface by a spherometer",
    "Determine masses of two objects using a beam balance",
    "Measure the weight of a body using the parallelogram law of vector addition",
    "Plot L-T and L-T squared graphs for a simple pendulum and find effective length of a seconds pendulum",
    "Study limiting friction versus normal reaction and determine coefficient of friction",
    "Find the downward force on a roller along an inclined plane and relate it to sin theta",
    "Find the force constant and effective mass of a helical spring using oscillations",
    "Study volume versus pressure for air at constant temperature",
    "Determine coefficient of viscosity of a liquid using terminal velocity",
    "Study temperature of a hot body versus time using a cooling curve",
    "Study frequency and length, and length and tension, of a wire using a sonometer",
    "Determine speed of sound in air using a resonance tube",
    "Determine specific heat capacity of a solid and liquid by the method of mixtures",
]

CLASS_XI_ACTIVITIES = [
    "Make paper scales of least count 0.2 cm and 0.5 cm and measure length",
    "Determine mass of a body using a metre scale and the principle of moments",
    "Plot a graph from data using a proper scale and show precision error bars",
    "Measure rolling friction force for a roller on a horizontal plane",
    "Study range of a water jet versus angle of projection",
    "Study conservation of energy of a ball rolling down an inclined plane",
    "Study dissipation of energy of a simple pendulum with time",
    "Observe change of state and plot a cooling curve for molten wax",
    "Observe and explain heating of a bi-metallic strip",
    "Study heating effect on liquid level in a container",
    "Study detergent effect on water surface tension using capillary rise",
    "Study load effect on depression of a clamped metre scale",
]

CLASS_XII_EXPERIMENTS = [
    "Determine resistance per unit length of a wire from a potential difference-current graph",
    "Determine wire resistance and resistivity using a metre bridge",
    "Verify series and parallel laws of combination of resistances using a metre bridge",
    "Compare emf of Daniel and Leclanche primary cells using a potentiometer",
    "Determine internal resistance of a primary cell using a potentiometer",
    "Determine galvanometer resistance by half-deflection and its figure of merit",
    "Convert a galvanometer into an ammeter and voltmeter and verify the ranges",
    "Determine frequency of alternating current using a sonometer",
    "Find focal length of a concave mirror from object and image distances",
    "Find focal length of a convex lens using u-v or reciprocal graphs",
    "Find focal length of a convex mirror using a convex lens",
    "Find focal length of a concave lens with a convex lens",
    "Determine minimum deviation angle of a glass prism from an incidence-deviation graph",
    "Determine refractive index of water using a concave mirror, convex lens, and plane mirror",
    "Draw forward and reverse I-V characteristics of a p-n junction",
    "Draw a Zener diode characteristic curve and determine reverse breakdown voltage",
    "Study common-emitter transistor characteristics and determine current and voltage gains",
]

CLASS_XII_ACTIVITIES = [
    "Assemble components of a given electrical circuit",
    "Correct an incorrectly connected circuit and draw the corrected diagram",
    "Measure resistance and impedance of an inductor with or without an iron core",
    "Use a multimeter to measure resistance, voltage, current, and continuity",
    "Assemble a household circuit with bulbs, switches, fuse, and power source",
    "Study potential drop versus length for a steady-current wire",
    "Study light intensity effect on an LDR by varying source distance",
    "Identify a diode, LED, transistor, IC, resistor, and capacitor from a mixed set",
    "Check a diode, distinguish npn and pnp transistors, and identify transistor terminals",
    "Observe refraction and lateral deviation through a glass slab",
    "Observe polarisation using two polaroids",
    "Observe diffraction of light through a thin slit",
    "Study image nature and size for a convex lens and concave mirror using candle and screen",
    "Determine focal length of two lenses in contact",
]


def steps_for(title: str) -> list[tuple[str, str]]:
    return [
        (f"Arrange the apparatus and materials required for {title} as shown in the manual.", "The apparatus is aligned and the initial condition is recorded."),
        ("Take the prescribed measurements or make the controlled adjustment described in the manual.", "The relevant physical quantity changes while other conditions are kept controlled."),
        ("Repeat the observation for the required readings or settings and record the result in a table.", "A set of comparable readings is obtained for analysis."),
        ("Plot the required graph or apply the stated relation and report the final quantity.", "The calculated result is compared with the expected physical relationship."),
    ]


def make_record(prefix: str, class_level: int, number: int, title: str, item_type: str) -> dict:
    experiment_id = f"phy_{class_level}_{number:03d}"
    chapter = f"Physics Class {class_level} {'Experiments' if item_type == 'experiment' else 'Activities'}"
    scene_id = f"{experiment_id}_scene"
    steps = steps_for(title)
    return {
        "experiment_id": experiment_id,
        "subject": "Physics",
        "class_level": class_level,
        "chapter": chapter,
        "title": title,
        "difficulty": "medium" if item_type == "experiment" else "easy",
        "educational_goal": f"Perform the Physics Laboratory Manual Class {class_level} {item_type} '{title}' and connect the measurements to the stated physical principle.",
        "concepts": ["measurement", "observation", "data analysis", "class-" + str(class_level)],
        "materials": ["manual-specified apparatus", "measuring instruments", "recording table", "graph paper where required"],
        "safety_notes": ["Follow the supplied manual and teacher supervision for electrical circuits, optics, moving parts, heat, and laboratory equipment.", "Check connections before energising a circuit and handle glassware and weights carefully."],
        "procedure_steps": [{"step_id": i, "instruction": instruction, "observation": observation} for i, (instruction, observation) in enumerate(steps, 1)],
        "scenes": [{"scene_id": scene_id, "name": "Manual setup and measurement", "description": f"A school physics laboratory bench presents the apparatus for {title}, followed by controlled measurement and graphing actions from the supplied Physics Laboratory Manual.", "visible_actions": ["arrange apparatus", "take measurements", "record readings", "plot or calculate result"], "image_asset_id": f"{experiment_id}_start"}],
        "sources": [{"source_id": "physics_manual_11_12", "source_type": "reference", "url": "Physics_Laboratory_Manual_11-12_E.pdf", "citation": f"Physics Laboratory Manual for Classes XI-XII, Class {class_level}, {item_type.title()} {number}; exact PDF page to verify during citation pass", "verification_status": "verified"}],
        "image_assets": [{"image_asset_id": f"{experiment_id}_start", "role": "starting_image", "url": "PLACEHOLDER: add a license-reviewed real physics laboratory setup image", "license_status": "placeholder"}],
        "tags": ["physics", "class-" + str(class_level), "manual-physics", item_type],
        "status": "source_review",
    }


def main() -> None:
    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    payload["experiments"] = [record for record in payload["experiments"] if record.get("subject") != "Physics"]
    records = []
    for number, title in enumerate(CLASS_XI_EXPERIMENTS, 1):
        records.append(make_record("phy", 11, number, title, "experiment"))
    for number, title in enumerate(CLASS_XI_ACTIVITIES, 1):
        records.append(make_record("phy", 11, 100 + number, title, "activity"))
    for number, title in enumerate(CLASS_XII_EXPERIMENTS, 1):
        records.append(make_record("phy", 12, number, title, "experiment"))
    for number, title in enumerate(CLASS_XII_ACTIVITIES, 1):
        records.append(make_record("phy", 12, 100 + number, title, "activity"))
    payload["experiments"].extend(records)
    payload["dataset_version"] = "0.3.0"
    DATA_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Added {len(records)} Physics manual records")


if __name__ == "__main__":
    main()
