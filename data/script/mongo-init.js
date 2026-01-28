const fs = require('fs');

const data = JSON.parse(
  fs.readFileSync('/docker-entrypoint-initdb.d/customer.json')
);

db = db.getSiblingDB('customerdb');

db.customers.insertMany(data.customers);

db.customers.createIndex({ customerid: 1 }, { unique: true });
db.customers.createIndex({ email: 1 }, { unique: true });

print('Customers successfully imported!');