mongosh "mongodb://127.0.0.1:27017/aiiinotate_benchmark" -f <<EOF 
use aiiinotate_benchmark;
console.log(db);

db.getCollection('annotations2').deleteMany({});
db.getCollection('manifests2').deleteMany({});
EOF
