Printers Database - Constraints and Behavior
Overview
This database uses comprehensive constraints to maintain data integrity and consistency. All constraints are enforced at the database level by SQLite.

Table Structure and Constraints
1. lieugestion (Locations)

Primary Key: StandortID
Unique: Standort - no duplicate location names
NOT NULL: Standort must have a value
CHECK: Location name cannot be empty or whitespace-only

Deletion Behavior:

❌ Cannot delete if referenced by any bureaus (RESTRICT)
❌ Cannot delete if referenced by any printernames (SET NULL instead)


2. fachabteilung (Departments)

Primary Key: FachabteilungID
Unique: Fachabteilung - no duplicate department names
NOT NULL: Fachabteilung must have a value
CHECK: Department name cannot be empty or whitespace-only

Deletion Behavior:

❌ Cannot delete if referenced by any bureaus (RESTRICT)


3. printermodels (Printer Models)

Primary Key: PrinterModel
CHECK: Model name cannot be empty or whitespace-only

Deletion Behavior:

❌ Cannot delete if referenced by any printernames (RESTRICT)


4. druckeinlage (Print Forms/Paper Types)

Primary Key: FormatDruckeinlage
CHECK Constraints:

WidthMM must be NULL or positive (> 0)
HeightMM must be NULL or positive (> 0)
Format name cannot be empty or whitespace-only



Deletion Behavior:

❌ Cannot delete if referenced by any caridocs (RESTRICT)


5. printersettings (Canon Printer Settings)

Primary Key: CanonPrinterSettings
CHECK: Settings name cannot be empty or whitespace-only
SettingsPNG: Optional binary data (BLOB)

Deletion Behavior:

❌ Cannot delete if referenced by any caridocs (RESTRICT)


6. caridocs (CARI Documents/Forms)

Primary Key: CARIdoc
NOT NULL: CARIdoc must have a value
CHECK: CARIdoc name cannot be empty or whitespace-only
Foreign Keys:

FormatDruckeinlage → druckeinlage (RESTRICT)
CanonPrinterSettings → printersettings (RESTRICT)



Deletion Behavior:

❌ Cannot delete if referenced by any slot_caridocs (RESTRICT)


7. printernames (Printers)

Primary Key: PrinterName
NOT NULL: PrinterName, PrinterModel must have values
CHECK: Printer name cannot be empty or whitespace-only
Foreign Keys:

PrinterModel → printermodels (RESTRICT)
StandortID → lieugestion (SET NULL - optional location)



Deletion Behavior:

✅ Can delete if printer has no slots
✅ Can delete if printer has slots with NO CARIdoc assignments
❌ Cannot delete if ANY slot has CARIdoc assignments in slot_caridocs
⚠️ Deleting a printer cascades deletion to all its slots in printerslots


8. printerslots (Printer Paper Trays/Slots)

Primary Key: (PrinterName, SlotName) - composite key
NOT NULL: PrinterName, SlotName, TwoSided, Inspect
DEFAULT: TwoSided = 0, Inspect = 0
CHECK: PrinterName and SlotName cannot be empty or whitespace-only
Foreign Keys:

PrinterName → printernames (CASCADE)



Deletion Behavior:

✅ Automatically deleted when parent printer is deleted (CASCADE)
❌ Cannot delete if slot has any CARIdoc assignments in slot_caridocs (RESTRICT)


9. bureaus (Bureaus/Offices)

Primary Key: BureauID
NOT NULL: Bureau, FachabteilungID, StandortID
UNIQUE: Bureau - bureau names are globally unique across all locations
CHECK: Bureau name cannot be empty or whitespace-only
Foreign Keys:

FachabteilungID → fachabteilung (RESTRICT)
StandortID → lieugestion (RESTRICT)



Deletion Behavior:

✅ Can delete if bureau has NO assignments in slot_caridocs
❌ Cannot delete if referenced by any slot_caridocs (RESTRICT)


10. slot_caridocs (Slot-CARIdoc Assignments)

Primary Key: (PrinterName, SlotName, CARIdoc, BureauID) - composite key
NOT NULL: All key fields must have values
CHECK: PrinterName, SlotName, and CARIdoc cannot be empty
Foreign Keys:

(PrinterName, SlotName) → printerslots (RESTRICT)
CARIdoc → caridocs (RESTRICT)
BureauID → bureaus (RESTRICT)



Deletion Behavior:

✅ Can always be deleted directly
⚠️ Blocks deletion of parent records (slots, caridocs, bureaus)


Special Business Rules
Database Trigger: Printer-Location Consistency
Rule: A printer can only serve bureaus from ONE location (Standort).
