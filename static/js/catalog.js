let cart = {};
let productsData = [];
let activeCategory = "all";
let activeSubcategory = "all";
let selectedProductForModal = null;

const CATALOG_STRUCTURE = {
  Алкоголь: ["Пиво и слабоалкогольные", "Крепкий алкоголь", "Закуски к пиву"],
  "Напитки, чай, кофе": ["Соки и газировка", "Вода и энергетики", "Чай и кофе"],
  "Молочка и яйца": [
    "Молоко",
    "Кефир и ряженка",
    "Йогурты и сметана",
    "Сыр",
    "Яйца",
  ],
  "Мясо, колбасы, консервы": [
    "Колбасы и сосиски",
    "Мясная продукция",
    "Консервы",
    "Овощи",
  ],
  "Заморозка и полуфабрикаты": [
    "Пельмени и манты",
    "Вареники",
    "Котлеты и голубцы",
    "Мороженое",
  ],
  "Крупы, мука, масла, специи": [
    "Крупы",
    "Мука",
    "Макаронные изделия",
    "Растительные масла",
    "Приправы и специи",
  ],
  "Сладости и снеки": [
    "Шоколад и конфеты",
    "Жвачки",
    "Чипсы, сухарики, попкорн",
    "Печенье и выпечка",
  ],
  Хлеб: ["Хлебобулочные изделия"],
  "Бытовая химия и гигиена": [
    "Шампуни и дезодоранты",
    "Мыло и уход за собой",
    "Стиральные порошки и моющие",
    "Хозяйственные мелочи",
  ],
};

// Переключение режимов темы: system -> light -> dark
function applyTheme(theme) {
  const isDark =
    theme === "dark" ||
    (theme === "system" &&
      window.matchMedia("(prefers-color-scheme: dark)").matches);
  document.documentElement.classList.toggle("dark", isDark);

  const btn = document.getElementById("theme-toggle-btn");
  if (btn) {
    if (theme === "system") btn.innerText = "💻 Авто";
    else if (theme === "light") btn.innerText = "☀️ Светлая";
    else if (theme === "dark") btn.innerText = "🌙 Тёмная";
  }
}

function cycleTheme() {
  const current = localStorage.getItem("theme") || "system";
  const next =
    current === "system" ? "light" : current === "light" ? "dark" : "system";
  localStorage.setItem("theme", next);
  applyTheme(next);
}

// Отслеживание смены системной темы на лету
window
  .matchMedia("(prefers-color-scheme: dark)")
  .addEventListener("change", () => {
    if ((localStorage.getItem("theme") || "system") === "system") {
      applyTheme("system");
    }
  });

// Скелетон с поддержкой Dark Mode
function showSkeleton() {
  const container = document.getElementById("catalog-container");
  if (!container) return;

  container.innerHTML = `
    <div class="grid grid-cols-2 sm:grid-cols-3 gap-3">
      ${Array(6)
        .fill(
          `
        <div class="bg-white dark:bg-gray-800 rounded-xl p-2.5 border border-gray-100 dark:border-gray-700/60 animate-pulse space-y-2">
          <div class="w-full h-28 bg-gray-200 dark:bg-gray-700 rounded-lg"></div>
          <div class="h-3 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
          <div class="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
          <div class="h-7 bg-gray-200 dark:bg-gray-700 rounded mt-2"></div>
        </div>
      `,
        )
        .join("")}
    </div>
  `;
}

// Заглушка с котом
function getEmptyStateHTML(
  title = "Раздел скоро заполнится",
  desc = "Завозим новые товары и наводим порядок на полках.",
) {
  return `
    <div class="col-span-full my-4 bg-gray-50 dark:bg-gray-800/60 border border-gray-200/80 dark:border-gray-700 rounded-2xl p-6 text-center relative overflow-hidden shadow-sm">
      <style>
        @keyframes gentleFloat {
          0%, 100% { transform: translateY(0) rotate(0deg); }
          50% { transform: translateY(-6px) rotate(1.5deg); }
        }
        @keyframes wrenchWiggle {
          0%, 100% { transform: rotate(0deg); }
          50% { transform: rotate(-15deg); }
        }
        .anim-cat-float { animation: gentleFloat 3s ease-in-out infinite; }
        .anim-wrench { animation: wrenchWiggle 2s ease-in-out infinite; transform-origin: 135px 125px; }
      </style>
      <div class="w-28 h-28 mx-auto mb-2 relative">
        <svg viewBox="0 0 200 200" fill="none" xmlns="http://www.w3.org/2000/svg" class="w-full h-full anim-cat-float">
          <ellipse cx="100" cy="175" rx="35" ry="5" fill="#334155"/>
          <path d="M135 140 C165 130, 160 90, 145 85" stroke="#475569" stroke-width="7" stroke-linecap="round" fill="none"/>
          <path d="M70 165 C65 120, 135 120, 130 165 Z" fill="#475569"/>
          <path d="M85 165 C82 135, 118 135, 115 165 Z" fill="#94A3B8"/>
          <circle cx="100" cy="95" r="38" fill="#475569"/>
          <path d="M68 75 L58 45 L85 62 Z" fill="#475569"/>
          <path d="M70 72 L62 49 L83 62 Z" fill="#F1F5F9"/>
          <path d="M132 75 L142 45 L115 62 Z" fill="#475569"/>
          <path d="M130 72 L138 49 L117 62 Z" fill="#F1F5F9"/>
          <path d="M82 92 Q89 85 94 92" stroke="#F1F5F9" stroke-width="3" stroke-linecap="round" fill="none"/>
          <path d="M106 92 Q111 85 118 92" stroke="#F1F5F9" stroke-width="3" stroke-linecap="round" fill="none"/>
          <polygon points="100,98 96,94 104,94" fill="#F43F5E"/>
          <path d="M96 102 Q100 106 104 102" stroke="#F1F5F9" stroke-width="2" stroke-linecap="round" fill="none"/>
          <line x1="62" y1="95" x2="80" y2="97" stroke="#94A3B8" stroke-width="2" stroke-linecap="round"/>
          <line x1="60" y1="102" x2="78" y2="101" stroke="#94A3B8" stroke-width="2" stroke-linecap="round"/>
          <line x1="138" y1="95" x2="120" y2="97" stroke="#94A3B8" stroke-width="2" stroke-linecap="round"/>
          <line x1="140" y1="102" x2="122" y2="101" stroke="#94A3B8" stroke-width="2" stroke-linecap="round"/>
          <path d="M68 72 C68 46, 132 46, 132 72 Z" fill="#F59E0B"/>
          <rect x="62" y="70" width="76" height="5" rx="2.5" fill="#D97706"/>
          <g class="anim-wrench">
            <path d="M130 135 L155 110" stroke="#CBD5E1" stroke-width="6" stroke-linecap="round"/>
            <circle cx="157" cy="108" r="6" stroke="#CBD5E1" stroke-width="3" fill="none"/>
          </g>
          <circle cx="125" cy="138" r="7" fill="#475569"/>
        </svg>
      </div>
      <h3 class="text-sm font-bold text-gray-800 dark:text-gray-200 mb-1">${title}</h3>
      <p class="text-xs text-gray-500 dark:text-gray-400 max-w-xs mx-auto leading-relaxed">${desc}</p>
      <span class="inline-block mt-3 bg-gray-200/70 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-[10px] font-bold px-3 py-1 rounded-full uppercase tracking-wider">В разработке</span>
    </div>
  `;
}

function updateStoreStatus() {
  const hour = new Date().getHours();
  const statusEl = document.getElementById("store-status");
  if (hour >= 9 && hour < 21) {
    statusEl.className =
      "inline-flex items-center gap-1 text-[11px] font-bold px-2 py-0.5 rounded-full bg-green-100 dark:bg-green-950/80 text-green-700 dark:text-green-300 border border-green-200 dark:border-green-800";
    statusEl.innerText = "🟢 Открыто";
  } else {
    statusEl.className =
      "inline-flex items-center gap-1 text-[11px] font-bold px-2 py-0.5 rounded-full bg-red-100 dark:bg-red-950/80 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-800";
    statusEl.innerText = "🔴 Закрыто";
  }
}

async function loadProducts() {
  showSkeleton();

  try {
    const response = await fetch("products.json");
    if (!response.ok) throw new Error("Не удалось прочитать JSON");
    productsData = await response.json();

    renderCategories();
    filterProducts();
  } catch (error) {
    document.getElementById("catalog-container").innerHTML =
      `<p class="text-center text-red-500 py-8 text-sm">Ошибка загрузки: ${error.message}</p>`;
  }
}

function translit(str) {
  const ru = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя";
  const en = [
    "a",
    "b",
    "v",
    "g",
    "d",
    "e",
    "yo",
    "zh",
    "z",
    "i",
    "y",
    "k",
    "l",
    "m",
    "n",
    "o",
    "p",
    "r",
    "s",
    "t",
    "u",
    "f",
    "h",
    "ts",
    "ch",
    "sh",
    "shch",
    "",
    "y",
    "",
    "e",
    "yu",
    "ya",
  ];
  let result = str.toLowerCase();
  for (let i = 0; i < ru.length; i++) {
    result = result.split(ru[i]).join(en[i]);
  }
  return result;
}

function renderCategories() {
  const categoriesNav = document.getElementById("categories-nav");
  const availableCategories = ["all", ...Object.keys(CATALOG_STRUCTURE)];

  categoriesNav.innerHTML = availableCategories
    .map(
      (cat) => `
      <button onclick="setCategory('${cat}')" class="px-3 py-1 text-xs font-semibold rounded-full whitespace-nowrap border transition-all ${
        cat === activeCategory
          ? "bg-green-600 text-white border-green-600 shadow-sm"
          : "bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700"
      }">
        ${cat === "all" ? "Все товары" : cat}
      </button>
    `,
    )
    .join("");

  renderSubcategories();
}

function renderSubcategories() {
  const subNav = document.getElementById("subcategories-nav");
  if (activeCategory === "all" || !CATALOG_STRUCTURE[activeCategory]) {
    subNav.classList.add("hidden");
    activeSubcategory = "all";
    return;
  }

  const subcats = CATALOG_STRUCTURE[activeCategory];
  subNav.classList.remove("hidden");
  const allSubcats = ["all", ...subcats];

  subNav.innerHTML = allSubcats
    .map(
      (sub) => `
      <button onclick="setSubcategory('${sub}')" class="px-2.5 py-0.5 text-[11px] font-medium rounded-full whitespace-nowrap border transition-all ${
        sub === activeSubcategory
          ? "bg-gray-800 dark:bg-gray-200 text-white dark:text-gray-900 border-gray-800 dark:border-gray-200"
          : "bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 border-gray-200 dark:border-gray-700 hover:bg-gray-200 dark:hover:bg-gray-700"
      }">
        ${sub === "all" ? "Все подкатегории" : sub}
      </button>
    `,
    )
    .join("");
}

function setCategory(cat) {
  activeCategory = cat;
  activeSubcategory = "all";
  renderCategories();
  filterProducts();
}

function setSubcategory(sub) {
  activeSubcategory = sub;
  renderSubcategories();
  filterProducts();
}

function filterProducts() {
  const rawQuery = document
    .getElementById("search-input")
    .value.toLowerCase()
    .trim();
  const queryTranslit = translit(rawQuery);

  const filtered = productsData.filter((item) => {
    const catName = item.category || "Прочее";
    const subName = item.subcategory || "";

    const matchesCat = activeCategory === "all" || catName === activeCategory;
    const matchesSubcat =
      activeSubcategory === "all" || subName === activeSubcategory;

    const nameLower = item.name.toLowerCase();
    const nameTranslit = translit(nameLower);

    const matchesSearch =
      !rawQuery ||
      nameLower.includes(rawQuery) ||
      nameTranslit.includes(rawQuery) ||
      nameLower.includes(queryTranslit) ||
      item.barcode.includes(rawQuery);

    return matchesCat && matchesSubcat && matchesSearch;
  });

  if (activeCategory === "all" && !rawQuery) {
    renderPlayMarketView();
  } else {
    renderGridView(filtered, rawQuery);
  }
}

function renderBillboard() {
  const saleProducts = productsData.filter(
    (p) => p.old_price && p.old_price > p.price,
  );
  if (saleProducts.length === 0) return "";

  const slidesHtml = saleProducts
    .map((item) => {
      const discountPercent = Math.round(
        ((item.old_price - item.price) / item.old_price) * 100,
      );
      return `
        <div onclick="openProductModal('${item.barcode}')" class="snap-center shrink-0 w-72 sm:w-80 bg-gradient-to-r from-red-500 to-orange-500 rounded-2xl p-3.5 text-white shadow-md relative overflow-hidden cursor-pointer active:scale-98 transition-transform">
          <span class="absolute top-2 right-2 bg-yellow-400 text-red-950 text-[10px] font-black px-2 py-0.5 rounded-full uppercase shadow">
            -${discountPercent}%
          </span>
          <div class="flex items-center gap-3">
            <div class="w-20 h-20 bg-white dark:bg-gray-800 rounded-xl shrink-0 p-1 flex items-center justify-center">
              ${
                item.image
                  ? `<img src="static/img/${item.image}" class="w-full h-full object-contain">`
                  : `<span class="text-xs text-gray-400">Нет фото</span>`
              }
            </div>
            <div class="flex-grow min-w-0">
              <span class="text-[9px] uppercase font-extrabold bg-black/20 px-1.5 py-0.5 rounded text-white/90">🔥 Товар дня</span>
              <h4 class="font-bold text-xs sm:text-sm leading-tight truncate mt-1">${item.name}</h4>
              <div class="flex items-baseline gap-1.5 mt-1">
                <span class="text-base font-black text-yellow-300">${item.price} ₸</span>
                <span class="text-xs line-through text-white/70">${item.old_price} ₸</span>
              </div>
            </div>
          </div>
        </div>
      `;
    })
    .join("");

  return `
    <section class="mb-6">
      <div class="flex justify-between items-center mb-2">
        <h2 class="text-base font-bold text-gray-800 dark:text-gray-200 flex items-center gap-1">
          <span>🔥 Горячие скидки</span>
        </h2>
        <span class="text-[11px] text-gray-400 dark:text-gray-500">Листай ➔</span>
      </div>
      <div class="flex gap-3 overflow-x-auto snap-x snap-mandatory no-scrollbar pb-2 -mx-3 px-3 sm:mx-0 sm:px-0">
        ${slidesHtml}
      </div>
    </section>
  `;
}

function renderCardHTML(item) {
  const hasDiscount = item.old_price && item.old_price > item.price;
  const discountPercent = hasDiscount
    ? Math.round(((item.old_price - item.price) / item.old_price) * 100)
    : 0;

  return `
    <article onclick="openProductModal('${item.barcode}')" class="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-2.5 flex flex-col justify-between hover:shadow-md transition-all border border-gray-100 dark:border-gray-700/60 h-full cursor-pointer relative group">
      <div>
        <div class="relative">
          ${
            item.image
              ? `<img src="static/img/${item.image}" alt="${item.name}" class="w-full h-28 object-cover rounded-lg mb-2 bg-gray-50 dark:bg-gray-900">`
              : `<div class="w-full h-28 bg-gray-50 dark:bg-gray-900 rounded-lg mb-2 flex items-center justify-center text-gray-300 dark:text-gray-600 text-xs border border-dashed border-gray-200 dark:border-gray-700">Нет фото</div>`
          }
          ${
            hasDiscount
              ? `<span class="absolute top-1 left-1 bg-red-600 text-white text-[9px] font-black px-1.5 py-0.5 rounded-full shadow">-${discountPercent}%</span>`
              : ""
          }
        </div>
        
        <div class="flex flex-wrap gap-1 mb-1">
          <span class="text-[9px] font-semibold bg-green-50 dark:bg-green-950/60 text-green-700 dark:text-green-300 px-1.5 py-0.5 rounded">${item.category || "Прочее"}</span>
          ${item.volume_weight ? `<span class="text-[9px] font-semibold bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 px-1.5 py-0.5 rounded">${item.volume_weight}</span>` : ""}
        </div>
        <h3 class="font-semibold text-xs sm:text-sm text-gray-800 dark:text-gray-100 leading-tight group-hover:text-green-600 dark:group-hover:text-green-400 transition-colors">${item.name}</h3>
        
        <div class="mt-1 flex items-baseline gap-1">
          <span class="text-green-600 dark:text-green-400 font-bold text-sm">${item.price} ₸</span>
          ${hasDiscount ? `<span class="text-[10px] line-through text-gray-400 dark:text-gray-500 font-semibold">${item.old_price} ₸</span>` : ""}
        </div>
      </div>
      <div onclick="event.stopPropagation()" class="mt-2.5 flex items-center justify-between bg-gray-50 dark:bg-gray-900/60 rounded-lg p-1 border border-gray-200 dark:border-gray-700">
        <button onclick="addToCart('${item.barcode}', -1)" class="w-7 h-7 flex items-center justify-center text-gray-600 dark:text-gray-300 font-bold hover:bg-gray-200 dark:hover:bg-gray-700 rounded active:scale-90 transition-transform">-</button>
        <span id="qty-${item.barcode}" class="text-xs font-bold text-gray-800 dark:text-gray-200 w-6 text-center">${cart[item.barcode]?.qty || 0}</span>
        <button onclick="addToCart('${item.barcode}', 1)" class="w-7 h-7 flex items-center justify-center text-green-600 dark:text-green-400 font-bold hover:bg-green-100 dark:hover:bg-green-900/50 rounded active:scale-90 transition-transform">+</button>
      </div>
    </article>
  `;
}

function renderPlayMarketView() {
  const container = document.getElementById("catalog-container");
  const categories = Object.keys(CATALOG_STRUCTURE);

  let html = renderBillboard();

  categories.forEach((cat) => {
    const itemsInCat = productsData.filter(
      (p) => (p.category || "Прочее") === cat,
    );

    if (itemsInCat.length === 0) {
      html += `
        <section class="mb-6">
          <div class="flex justify-between items-center mb-2">
            <h2 class="text-base font-bold text-gray-800 dark:text-gray-200"><span>${cat}</span></h2>
          </div>
          ${getEmptyStateHTML(`Категория «${cat}» наполняется`, "Товары скоро появятся в продаже.")}
        </section>
      `;
      return;
    }

    html += `
      <section class="mb-6">
        <div class="flex justify-between items-center mb-2">
          <h2 class="text-base font-bold text-gray-800 dark:text-gray-200 flex items-center gap-1.5">
            <span>${cat}</span>
            <span class="text-xs font-normal text-gray-400 dark:text-gray-500">(${itemsInCat.length})</span>
          </h2>
          <button onclick="setCategory('${cat}')" class="text-xs font-bold text-green-600 dark:text-green-400 hover:underline">Все ➔</button>
        </div>
        <div class="flex gap-3 overflow-x-auto no-scrollbar pb-2 -mx-3 px-3 sm:mx-0 sm:px-0">
          ${itemsInCat.map((item) => `<div class="w-36 sm:w-44 flex-shrink-0">${renderCardHTML(item)}</div>`).join("")}
        </div>
      </section>
    `;
  });

  container.innerHTML = html;
}

function renderGridView(items, rawQuery) {
  const container = document.getElementById("catalog-container");
  if (items.length === 0) {
    const title = rawQuery
      ? `По запросу «${rawQuery}» ничего не найдено`
      : "Раздел скоро заполнится";
    container.innerHTML = getEmptyStateHTML(
      title,
      "Попробуйте изменить поиск или зайти позже.",
    );
    return;
  }

  container.innerHTML = `
    <ul class="grid grid-cols-2 sm:grid-cols-3 gap-3">
      ${items.map((item) => `<li>${renderCardHTML(item)}</li>`).join("")}
    </ul>
  `;
}

function openProductModal(barcode) {
  const product = productsData.find((p) => p.barcode === barcode);
  if (!product) return;

  selectedProductForModal = product;

  document.getElementById("modalName").innerText = product.name;
  document.getElementById("modalPrice").innerText = `${product.price} ₸`;
  document.getElementById("modalBarcode").innerText =
    `Штрихкод: ${product.barcode}`;
  document.getElementById("modalCat").innerText = product.category || "Прочее";

  const subcatEl = document.getElementById("modalSubcat");
  if (product.subcategory) {
    subcatEl.innerText = product.subcategory;
    subcatEl.classList.remove("hidden");
  } else {
    subcatEl.classList.add("hidden");
  }

  const volEl = document.getElementById("modalVolume");
  if (product.volume_weight) {
    volEl.innerText = product.volume_weight;
    volEl.classList.remove("hidden");
  } else {
    volEl.classList.add("hidden");
  }

  const mainImg = document.getElementById("modalMainImg");
  const noImg = document.getElementById("modalNoImg");

  const imagesList = Array.isArray(product.images)
    ? product.images
    : product.image
      ? [product.image]
      : [];

  if (imagesList.length > 0) {
    mainImg.src = `static/img/${imagesList[0]}`;
    mainImg.classList.remove("hidden");
    noImg.classList.add("hidden");
  } else {
    mainImg.classList.add("hidden");
    noImg.classList.remove("hidden");
  }

  updateModalCartControls();
  document.getElementById("productDetailModal").classList.remove("hidden");
}

function closeProductModal() {
  document.getElementById("productDetailModal").classList.add("hidden");
  selectedProductForModal = null;
}

function updateModalCartControls() {
  if (!selectedProductForModal) return;
  const b = selectedProductForModal.barcode;
  const qty = cart[b]?.qty || 0;

  const controls = document.getElementById("modalCartControls");
  controls.innerHTML = `
    <button onclick="addToCart('${b}', -1); updateModalCartControls();" class="w-8 h-8 flex items-center justify-center text-gray-600 dark:text-gray-300 font-bold hover:bg-gray-100 dark:hover:bg-gray-700 rounded text-base active:scale-90 transition-transform">-</button>
    <span class="text-base font-bold text-gray-800 dark:text-gray-100 w-8 text-center">${qty}</span>
    <button onclick="addToCart('${b}', 1); updateModalCartControls();" class="w-8 h-8 flex items-center justify-center text-green-600 dark:text-green-400 font-bold hover:bg-green-50 dark:hover:bg-green-950 rounded text-base active:scale-90 transition-transform">+</button>
  `;
}

function addToCart(barcode, change) {
  if (navigator.vibrate) navigator.vibrate(25);

  const product = productsData.find((p) => p.barcode === barcode);
  if (!product) return;

  if (!cart[barcode])
    cart[barcode] = { name: product.name, price: product.price, qty: 0 };

  cart[barcode].qty += change;
  if (cart[barcode].qty <= 0) delete cart[barcode];

  document.querySelectorAll(`#qty-${barcode}`).forEach((el) => {
    el.innerText = cart[barcode] ? cart[barcode].qty : 0;
  });

  updateCartUI();
}

function updateCartUI() {
  const cartBar = document.getElementById("cart-bar");
  const totalEl = document.getElementById("cart-total");

  let total = 0;
  let count = 0;

  for (let id in cart) {
    total += cart[id].price * cart[id].qty;
    count += cart[id].qty;
  }

  totalEl.innerText = `${total} ₸`;

  if (count > 0) {
    cartBar.classList.remove("translate-y-full");
  } else {
    cartBar.classList.add("translate-y-full");
  }
}

function checkout() {
  const phone = "77774614003";
  let text = "Здравствуйте! Мой заказ:\n\n";
  let total = 0;

  for (let id in cart) {
    const item = cart[id];
    text += `— ${item.name} (${item.qty} шт.) = ${item.price * item.qty} ₸\n`;
    total += item.price * item.qty;
  }

  text += `\nИтого к оплате: ${total} ₸`;

  window.open(
    `https://wa.me/${phone}?text=${encodeURIComponent(text)}`,
    "_blank",
  );
}

document.addEventListener("DOMContentLoaded", () => {
  applyTheme(localStorage.getItem("theme") || "system");
  updateStoreStatus();
  loadProducts();
});
