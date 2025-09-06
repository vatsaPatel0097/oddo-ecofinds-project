 EcoFinds 🛍️
> A second-hand marketplace built for the hackathon — buy & sell quality used goods, thoughtfully.

---

🚀 Features

- **User Authentication**
  - Register with email, username, and password (hashed for safety)
  - Login / Logout sessions
  - Editable profile (username, email, password, avatar upload)

- **User Dashboard**
  - View and update profile
  - Manage own listings (create / edit / delete)
  - See previous purchases
  - Quick link to Cart

- **Product Listings**
  - Create new listings with title, description, price, category, and images
  - Browse all available products with image, price, and title
  - Category filtering + keyword search
  - Product detail view with full specs

- **Shopping Cart**
  - Add to cart (with stock validation)
  - Update quantity / remove items
  - Checkout creates an Order and reduces stock

- **Orders**
  - View past purchases
  - Order detail page with items + totals

---

 🏗️ Tech Stack

- **Backend**: Django 5, SQLite (default database)
- **Frontend**: Django templates + Bootstrap 5 + custom CSS
- **Storage**: Local file system for media (images)
- **Other**: Pillow (image handling)


## ⚙️ Setup Instructions

 1. Clone repo
```bash
git clone https://github.com/YOUR_USERNAME/ecofinds.git
cd ecofinds
