TRIGGER_SPLASHTAG_QUERY = (
    "CREATE TRIGGER insert_splashtag "
    "BEFORE INSERT ON xscraper.players "
    "FOR EACH ROW "
    "EXECUTE FUNCTION insert_splashtag()"
)
