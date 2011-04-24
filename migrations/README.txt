This is the database migration directory for Schematic.

More info: https://github.com/jbalogh/schematic

If you used syncdb you'll probably just need to update to the
the latest migration.  Find the highest numbered script (say, 99) and
type this from the root dir::

  ./vendor/src/schematic/schematic -u 99 migrations

After that, run migrations like this::

  ./vendor/src/schematic/schematic migrations
