// Set up indexes in MongoDB
db.ip.createIndex({"events_meta.total":-1},{background: true})
db.ip.createIndex({"geo.ctry":1},{background: true})
db.ip.createIndex({"ts_added":-1},{background: true})
//db.ip.createIndex({"ts_last_update":-1},{background: true}) // not needed anywhere
db.ip.createIndex({"last_activity":-1},{background: true})
db.ip.createIndex({"hostname":1},{background: true})
db.ip.createIndex({"bl.n": 1, "bl.v": 1},{partialFilterExpression: {"bl": {$exists: true}}, background: true} )
db.ip.createIndex({"dbl.n": 1, "dbl.v": 1},{partialFilterExpression: {"dbl": {$exists: true}}, background: true} )
db.ip.createIndex({"rep":-1},{background: true})
db.ip.createIndex({"bgppref":1},{background: true})
db.ip.createIndex({"ipblock":1},{background: true})
db.asn.createIndex({"org":1},{background: true})
db.ipblock.createIndex({"org":1},{background: true})

// Needed by Updater
//db.ip.createIndex({"_nru4h": 1},{background: true})
db.ip.createIndex({"_nru1d": 1},{background: true})
db.ip.createIndex({"_nru1w": 1},{background: true})
//db.asn.createIndex({"_nru4h": 1},{background: true})
db.asn.createIndex({"_nru1d": 1},{background: true})
db.asn.createIndex({"_nru1w": 1},{background: true})

// Needed by munin nerd_delay plugin
db.ip.createIndex({"_ttl.warden":-1},{background: true})
