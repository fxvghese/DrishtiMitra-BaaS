-- ==============================================================================
-- Migration: 20260911000001_phase3_rules.sql
-- Description: Seed compliance rules for Phase 3 (Rules 6, 10, 11, 12, 13, 14, 16, 17, 24, 26)
-- Database: PostgreSQL / Supabase
-- ==============================================================================

INSERT INTO rules (rule_code, name, description, field_name, validation_type, required, severity, active)
VALUES
    (
        'LM006',
        'Rule 6 - Declarations to be made on every package',
        'Verifies mandatory package declarations including responsible party, commodity name, net quantity, MRP, date, and consumer care.',
        'manufacturer',
        'PRESENT',
        TRUE,
        'HIGH',
        TRUE
    ),
    (
        'LM010',
        'Rule 10 - Name and address of manufacturer, packer, importer',
        'Verifies complete address declaration of manufacturer, packer, or importer.',
        'manufacturer',
        'PRESENT',
        TRUE,
        'HIGH',
        TRUE
    ),
    (
        'LM011',
        'Rule 11 - General provisions relating to declaration of quantity',
        'Verifies quantity exclusions, wrapper tares, and permitted when-packed qualifiers.',
        'net_quantity',
        'VALID_QUANTITY',
        TRUE,
        'HIGH',
        TRUE
    ),
    (
        'LM012',
        'Rule 12 - Manner in which declaration of quantity shall be made',
        'Verifies unit mode, absence of exaggerated/misleading wording, and small package devices.',
        'net_quantity',
        'VALID_QUANTITY',
        TRUE,
        'HIGH',
        TRUE
    ),
    (
        'LM013',
        'Rule 13 - Statement of units of weight, measure or number',
        'Verifies permitted SI units, symbols, prohibited count names (dozen, score, etc.), and unit scaling.',
        'net_quantity',
        'VALID_UNIT',
        TRUE,
        'HIGH',
        TRUE
    ),
    (
        'LM014',
        'Rule 14 - Dimensions of certain commodities',
        'Verifies number and finished dimensions for textiles, dhoties, sarees, bed-sheets, etc.',
        'dimensions',
        'VALID_DIMENSIONS',
        FALSE,
        'MEDIUM',
        TRUE
    ),
    (
        'LM016',
        'Rule 16 - Declarations with regard to number of usable sheets',
        'Verifies number of usable sheets and sheet dimensions for sheet-type commodities.',
        'sheets',
        'PRESENT',
        FALSE,
        'MEDIUM',
        TRUE
    ),
    (
        'LM017',
        'Rule 17 - Dimensions of container-type commodities',
        'Verifies count and shape-appropriate dimensions and capacity references for container-type commodities.',
        'container',
        'VALID_DIMENSIONS',
        FALSE,
        'MEDIUM',
        TRUE
    ),
    (
        'LM024',
        'Rule 24 - Declarations applicable to every wholesale package',
        'Verifies wholesale package identity, responsible entity address, and total quantity or retail package count.',
        'wholesale',
        'PRESENT',
        FALSE,
        'HIGH',
        TRUE
    ),
    (
        'LM026',
        'Rule 26 - Exemption in respect of certain packages',
        'Assesses applicability and exemption conditions (small quantity, fast food, DPCO, agricultural produce, pan masala 2026 proviso).',
        'exemption',
        'EXEMPTION_CHECK',
        FALSE,
        'LOW',
        TRUE
    )
ON CONFLICT (rule_code) DO UPDATE
SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    field_name = EXCLUDED.field_name,
    validation_type = EXCLUDED.validation_type,
    required = EXCLUDED.required,
    severity = EXCLUDED.severity,
    active = EXCLUDED.active,
    updated_at = NOW();
