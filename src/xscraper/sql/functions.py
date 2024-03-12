FUNCTION_SPLASHTAG_QUERY = (
    "CREATE OR REPLACE FUNCTION insert_splashtag() "
    "RETURNS TRIGGER AS $$ "
    "BEGIN "
    "NEW.splashtag = NEW.name || '#' || NEW.name_id; "
    "RETURN NEW; "
    "END; "
    "$$ LANGUAGE plpgsql"
)
