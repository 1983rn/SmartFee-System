-- Add missing columns to school_configuration table
ALTER TABLE school_configuration ADD COLUMN school_address TEXT;
ALTER TABLE school_configuration ADD COLUMN head_teacher_contact TEXT;
ALTER TABLE school_configuration ADD COLUMN bursar_contact TEXT;
ALTER TABLE school_configuration ADD COLUMN school_email TEXT;
