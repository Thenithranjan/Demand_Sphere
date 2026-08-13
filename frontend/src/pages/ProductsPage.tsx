/**
 * Products Page — Retail AI Frontend
 * =====================================
 * Modern searchable data table with filters, CRUD operations,
 * and detailed product views.
 */

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Plus, Eye, Pencil, Trash2, X } from 'lucide-react';
import { useProducts } from '../hooks';
import DataTable, { type Column } from '../components/shared/DataTable';
import StatusBadge from '../components/shared/StatusBadge';
import { useTheme } from '../contexts/ThemeContext';
import { cn, formatCurrency } from '../utils';
import { fadeIn } from '../animations/variants';
import type { Product } from '../types';
import { productApi as productService } from '../services/productApi';
import { useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

export default function ProductsPage() {
  const { isDark } = useTheme();
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [filters, setFilters] = useState({ category: '', brand: '', status: '' });
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);

  const { data, isLoading } = useProducts({
    skip: (page - 1) * pageSize,
    limit: pageSize,
    category: filters.category || undefined,
    brand: filters.brand || undefined,
    status: filters.status || undefined,
  });

  const columns: Column<Product>[] = [
    { key: 'ProductID', label: 'ID', sortable: true, className: 'font-mono text-xs' },
    {
      key: 'ProductName', label: 'Product', sortable: true,
      render: (item) => (
        <div>
          <p className={cn('font-medium', isDark ? 'text-zinc-200' : 'text-zinc-800')}>{item.ProductName}</p>
          <p className="text-xs text-zinc-500">{item.Brand}</p>
        </div>
      ),
    },
    { key: 'Category', label: 'Category', sortable: true },
    { key: 'SubCategory', label: 'Sub-Category' },
    {
      key: 'Price', label: 'Price', sortable: true,
      render: (item) => <span className="font-medium text-emerald-500">{formatCurrency(item.Price)}</span>,
    },
    { key: 'Fabric', label: 'Fabric' },
    {
      key: 'ProductStatus', label: 'Status',
      render: (item) => <StatusBadge status={item.ProductStatus || 'Active'} />,
    },
  ];

  const handleDelete = async (product: Product) => {
    if (!confirm(`Delete "${product.ProductName}"?`)) return;
    try {
      await productService.delete(product.ProductID);
      toast.success('Product deleted successfully');
      queryClient.invalidateQueries({ queryKey: ['products'] });
      queryClient.invalidateQueries({ queryKey: ['inventory'] });
    } catch {
      toast.error('Failed to delete product');
    }
  };

  const handleAddSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const newProduct = {
      ProductID: formData.get('ProductID') as string,
      SKU: formData.get('SKU') as string,
      ProductName: formData.get('ProductName') as string,
      Category: formData.get('Category') as string,
      SubCategory: formData.get('SubCategory') as string,
      Brand: formData.get('Brand') as string,
      Color: (formData.get('Color') as string) || undefined,
      Size: (formData.get('Size') as string) || undefined,
      Fabric: (formData.get('Fabric') as string) || undefined,
      SeasonalDemandTag: (formData.get('SeasonalDemandTag') as string) || undefined,
      Gender: (formData.get('Gender') as string) || undefined,
      Price: parseFloat(formData.get('Price') as string),
      CostPrice: parseFloat(formData.get('CostPrice') as string),
      SupplierID: formData.get('SupplierID') as string,
      ProductStatus: (formData.get('ProductStatus') as string) || 'Active',
      ImageURL: (formData.get('ImageURL') as string) || undefined,
    };

    try {
      await productService.create(newProduct);
      toast.success('Product added successfully');
      setIsAddModalOpen(false);
      queryClient.invalidateQueries({ queryKey: ['products'] });
      queryClient.invalidateQueries({ queryKey: ['inventory'] });
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to add product';
      toast.error(errorMsg);
    }
  };

  const handleEditSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!editingProduct) return;
    const formData = new FormData(e.currentTarget);
    const updatedProduct = {
      ProductName: formData.get('ProductName') as string,
      Category: formData.get('Category') as string,
      SubCategory: formData.get('SubCategory') as string,
      Brand: formData.get('Brand') as string,
      Color: (formData.get('Color') as string) || undefined,
      Size: (formData.get('Size') as string) || undefined,
      Fabric: (formData.get('Fabric') as string) || undefined,
      SeasonalDemandTag: (formData.get('SeasonalDemandTag') as string) || undefined,
      Gender: (formData.get('Gender') as string) || undefined,
      Price: parseFloat(formData.get('Price') as string),
      CostPrice: parseFloat(formData.get('CostPrice') as string),
      SupplierID: formData.get('SupplierID') as string,
      ProductStatus: (formData.get('ProductStatus') as string) || 'Active',
      ImageURL: (formData.get('ImageURL') as string) || undefined,
    };

    try {
      await productService.update(editingProduct.ProductID, updatedProduct);
      toast.success('Product updated successfully');
      setEditingProduct(null);
      queryClient.invalidateQueries({ queryKey: ['products'] });
      queryClient.invalidateQueries({ queryKey: ['inventory'] });
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || 'Failed to update product';
      toast.error(errorMsg);
    }
  };

  return (
    <motion.div variants={fadeIn} initial="hidden" animate="visible" className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className={cn('text-2xl font-bold', isDark ? 'text-zinc-100' : 'text-zinc-900')}>Products</h1>
          <p className="text-sm text-zinc-500 mt-1">Manage your product catalog • {data?.total ?? 0} products</p>
        </div>
        <motion.button
          onClick={() => setIsAddModalOpen(true)}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium text-white gradient-brand hover:opacity-90 transition-opacity"
        >
          <Plus className="w-4 h-4" /> Add Product
        </motion.button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        {/* Category Dropdown */}
        <select
          value={filters.category}
          onChange={(e) => setFilters((f) => ({ ...f, category: e.target.value }))}
          className={cn(
            'px-3 py-1.5 rounded-xl text-sm outline-none border transition-colors cursor-pointer',
            isDark
              ? 'bg-zinc-800 border-zinc-700 text-zinc-300 focus:border-brand-500'
              : 'bg-white border-zinc-200 text-zinc-700 focus:border-brand-500'
          )}
        >
          <option value="">All Categories</option>
          {['Men', 'Women', 'Home & Lifestyle', 'Kids', 'Accessories'].map((cat) => (
            <option key={cat} value={cat}>{cat}</option>
          ))}
        </select>

        {/* Brand Dropdown */}
        <select
          value={filters.brand}
          onChange={(e) => setFilters((f) => ({ ...f, brand: e.target.value }))}
          className={cn(
            'px-3 py-1.5 rounded-xl text-sm outline-none border transition-colors cursor-pointer',
            isDark
              ? 'bg-zinc-800 border-zinc-700 text-zinc-300 focus:border-brand-500'
              : 'bg-white border-zinc-200 text-zinc-700 focus:border-brand-500'
          )}
        >
          <option value="">All Brands</option>
          {['Ramraj Cotton', 'Uathayam', 'Biba', 'Fabindia', 'Prisma', 'Westside', 'Guess', 'Netplay', 'Kanchipuram Handloom', 'Raymond', 'Nandu Lungi'].map((brand) => (
            <option key={brand} value={brand}>{brand}</option>
          ))}
        </select>

        {/* Status Dropdown */}
        <select
          value={filters.status}
          onChange={(e) => setFilters((f) => ({ ...f, status: e.target.value }))}
          className={cn(
            'px-3 py-1.5 rounded-xl text-sm outline-none border transition-colors cursor-pointer',
            isDark
              ? 'bg-zinc-800 border-zinc-700 text-zinc-300 focus:border-brand-500'
              : 'bg-white border-zinc-200 text-zinc-700 focus:border-brand-500'
          )}
        >
          <option value="">All Statuses</option>
          {['Active', 'Inactive', 'Discontinued'].map((status) => (
            <option key={status} value={status}>{status}</option>
          ))}
        </select>
      </div>

      {/* Table */}
      <DataTable
        data={data?.items ?? []}
        columns={columns}
        isLoading={isLoading}
        searchPlaceholder="Search products..."
        searchKeys={['ProductName', 'Brand', 'Category', 'ProductID']}
        totalItems={data?.total}
        page={page}
        pageSize={pageSize}
        onPageChange={setPage}
        onPageSizeChange={(s) => { setPageSize(s); setPage(1); }}
        actions={(item) => (
          <div className="flex items-center gap-1">
            <button
              onClick={() => setSelectedProduct(item)}
              className="p-1.5 rounded-lg text-zinc-500 hover:text-brand-400 hover:bg-brand-500/10 transition-colors"
            >
              <Eye className="w-4 h-4" />
            </button>
            <button
              onClick={() => setEditingProduct(item)}
              className="p-1.5 rounded-lg text-zinc-500 hover:text-amber-400 hover:bg-amber-500/10 transition-colors"
            >
              <Pencil className="w-4 h-4" />
            </button>
            <button
              onClick={() => handleDelete(item)}
              className="p-1.5 rounded-lg text-zinc-500 hover:text-red-400 hover:bg-red-500/10 transition-colors"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        )}
      />

      {/* Product Detail Modal */}
      {selectedProduct && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
          onClick={() => setSelectedProduct(null)}
        >
          <motion.div
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            onClick={(e) => e.stopPropagation()}
            className={cn(
              'w-full max-w-lg rounded-2xl p-6 border',
              isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-zinc-200'
            )}
          >
            <div className="flex items-center justify-between mb-4">
              <h2 className={cn('text-lg font-bold', isDark ? 'text-zinc-100' : 'text-zinc-900')}>Product Details</h2>
              <button onClick={() => setSelectedProduct(null)} className="text-zinc-500 hover:text-zinc-300">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="space-y-3">
              {[
                ['Product ID', selectedProduct.ProductID],
                ['Name', selectedProduct.ProductName],
                ['SKU', selectedProduct.SKU],
                ['Category', `${selectedProduct.Category} / ${selectedProduct.SubCategory}`],
                ['Brand', selectedProduct.Brand],
                ['Price', formatCurrency(selectedProduct.Price)],
                ['Cost Price', formatCurrency(selectedProduct.CostPrice)],
                ['Fabric', selectedProduct.Fabric],
                ['Color', selectedProduct.Color],
                ['Size', selectedProduct.Size],
                ['Gender', selectedProduct.Gender],
                ['Status', selectedProduct.ProductStatus],
              ].map(([label, value]) => (
                <div key={label} className="flex justify-between text-sm">
                  <span className="text-zinc-500">{label}</span>
                  <span className={isDark ? 'text-zinc-200' : 'text-zinc-800'}>{value || '—'}</span>
                </div>
              ))}
            </div>
          </motion.div>
        </motion.div>
      )}

      {/* Add Product Modal */}
      {isAddModalOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 overflow-y-auto"
          onClick={() => setIsAddModalOpen(false)}
        >
          <motion.div
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            onClick={(e) => e.stopPropagation()}
            className={cn(
              'w-full max-w-xl rounded-2xl p-6 border my-8',
              isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-zinc-200'
            )}
          >
            <div className="flex items-center justify-between mb-4">
              <h2 className={cn('text-lg font-bold', isDark ? 'text-zinc-100' : 'text-zinc-900')}>Add New Product</h2>
              <button onClick={() => setIsAddModalOpen(false)} className="text-zinc-500 hover:text-zinc-300">
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleAddSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-zinc-400 mb-1">Product ID</label>
                  <input
                    type="text"
                    name="ProductID"
                    required
                    placeholder="e.g. P0501"
                    defaultValue={data ? `P${String(data.total + 1).padStart(4, '0')}` : ''}
                    className={cn(
                      'w-full px-3 py-2 rounded-xl text-sm outline-none border transition-colors',
                      isDark
                        ? 'bg-zinc-800 border-zinc-700 text-zinc-100 focus:border-brand-500'
                        : 'bg-white border-zinc-200 text-zinc-900 focus:border-brand-500'
                    )}
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-zinc-400 mb-1">SKU</label>
                  <input
                    type="text"
                    name="SKU"
                    required
                    placeholder="e.g. RAM-VESH-0501"
                    className={cn(
                      'w-full px-3 py-2 rounded-xl text-sm outline-none border transition-colors',
                      isDark
                        ? 'bg-zinc-800 border-zinc-700 text-zinc-100 focus:border-brand-500'
                        : 'bg-white border-zinc-200 text-zinc-900 focus:border-brand-500'
                    )}
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-zinc-400 mb-1">Product Name</label>
                <input
                  type="text"
                  name="ProductName"
                  required
                  placeholder="e.g. Ramraj Cotton White Veshti"
                  className={cn(
                    'w-full px-3 py-2 rounded-xl text-sm outline-none border transition-colors',
                    isDark
                      ? 'bg-zinc-800 border-zinc-700 text-zinc-100 focus:border-brand-500'
                      : 'bg-white border-zinc-200 text-zinc-900 focus:border-brand-500'
                  )}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-zinc-400 mb-1">Category</label>
                  <input
                    type="text"
                    name="Category"
                    required
                    list="add-category-list"
                    placeholder="Select or type Category"
                    className={cn(
                      'w-full px-3 py-2 rounded-xl text-sm outline-none border transition-colors',
                      isDark
                        ? 'bg-zinc-800 border-zinc-700 text-zinc-100 focus:border-brand-500'
                        : 'bg-white border-zinc-200 text-zinc-900 focus:border-brand-500'
                    )}
                  />
                  <datalist id="add-category-list">
                    {['Men', 'Women', 'Kids', 'Accessories', 'Home & Lifestyle'].map((c) => (
                      <option key={c} value={c} />
                    ))}
                  </datalist>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-zinc-400 mb-1">Sub-Category</label>
                  <input
                    type="text"
                    name="SubCategory"
                    required
                    placeholder="e.g. Veshti"
                    className={cn(
                      'w-full px-3 py-2 rounded-xl text-sm outline-none border transition-colors',
                      isDark
                        ? 'bg-zinc-800 border-zinc-700 text-zinc-100 focus:border-brand-500'
                        : 'bg-white border-zinc-200 text-zinc-900 focus:border-brand-500'
                    )}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-zinc-400 mb-1">Brand</label>
                  <input
                    type="text"
                    name="Brand"
                    required
                    list="add-brand-list"
                    placeholder="Select or type Brand"
                    className={cn(
                      'w-full px-3 py-2 rounded-xl text-sm outline-none border transition-colors',
                      isDark
                        ? 'bg-zinc-800 border-zinc-700 text-zinc-100 focus:border-brand-500'
                        : 'bg-white border-zinc-200 text-zinc-900 focus:border-brand-500'
                    )}
                  />
                  <datalist id="add-brand-list">
                    {['Ramraj Cotton', 'Uathayam', 'Biba', 'Fabindia', 'Prisma', 'Westside', 'Guess', 'Netplay', 'Kanchipuram Handloom', 'Raymond', 'Nandu Lungi'].map((brand) => (
                      <option key={brand} value={brand} />
                    ))}
                  </datalist>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-zinc-400 mb-1">Fabric</label>
                  <input
                    type="text"
                    name="Fabric"
                    required
                    list="add-fabric-list"
                    placeholder="Select or type Fabric"
                    className={cn(
                      'w-full px-3 py-2 rounded-xl text-sm outline-none border transition-colors',
                      isDark
                        ? 'bg-zinc-800 border-zinc-700 text-zinc-100 focus:border-brand-500'
                        : 'bg-white border-zinc-200 text-zinc-900 focus:border-brand-500'
                    )}
                  />
                  <datalist id="add-fabric-list">
                    {['Cotton', 'Silk', 'Handloom', 'Polyester', 'Polyester Blend', 'Linen', 'Leather'].map((fabric) => (
                      <option key={fabric} value={fabric} />
                    ))}
                  </datalist>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-zinc-400 mb-1">Price (₹)</label>
                  <input
                    type="number"
                    name="Price"
                    step="0.01"
                    required
                    placeholder="0.00"
                    className={cn(
                      'w-full px-3 py-2 rounded-xl text-sm outline-none border transition-colors',
                      isDark
                        ? 'bg-zinc-800 border-zinc-700 text-zinc-100 focus:border-brand-500'
                        : 'bg-white border-zinc-200 text-zinc-900 focus:border-brand-500'
                    )}
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-zinc-400 mb-1">Cost Price (₹)</label>
                  <input
                    type="number"
                    name="CostPrice"
                    step="0.01"
                    required
                    placeholder="0.00"
                    className={cn(
                      'w-full px-3 py-2 rounded-xl text-sm outline-none border transition-colors',
                      isDark
                        ? 'bg-zinc-800 border-zinc-700 text-zinc-100 focus:border-brand-500'
                        : 'bg-white border-zinc-200 text-zinc-900 focus:border-brand-500'
                    )}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-zinc-400 mb-1">Supplier</label>
                  <select
                    name="SupplierID"
                    required
                    className={cn(
                      'w-full px-3 py-2 rounded-xl text-sm outline-none border transition-colors cursor-pointer',
                      isDark
                        ? 'bg-zinc-800 border-zinc-700 text-zinc-100 focus:border-brand-500'
                        : 'bg-white border-zinc-200 text-zinc-900 focus:border-brand-500'
                    )}
                  >
                    <option value="SUP001">Ramraj Cotton</option>
                    <option value="SUP002">Raymond</option>
                    <option value="SUP003">Biba</option>
                    <option value="SUP004">Fabindia</option>
                    <option value="SUP005">Westside</option>
                    <option value="SUP006">Uathayam</option>
                    <option value="SUP007">Prisma</option>
                    <option value="SUP008">Guess</option>
                    <option value="SUP009">Nandu Lungi</option>
                    <option value="SUP010">Peter England</option>
                    <option value="SUP011">Louis Philippe</option>
                    <option value="SUP012">Allen Solly</option>
                    <option value="SUP013">Van Heusen</option>
                    <option value="SUP014">Levi's</option>
                    <option value="SUP015">Pepe Jeans</option>
                    <option value="SUP016">US Polo</option>
                    <option value="SUP017">Arrow</option>
                    <option value="SUP018">Nike</option>
                    <option value="SUP019">Adidas</option>
                    <option value="SUP020">Puma</option>
                    <option value="SUP021">Campus</option>
                    <option value="SUP022">Jockey</option>
                    <option value="SUP023">Lux</option>
                    <option value="SUP024">VIP</option>
                    <option value="SUP025">Wildcraft</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-zinc-400 mb-1">Status</label>
                  <input
                    type="text"
                    name="ProductStatus"
                    list="add-status-list"
                    defaultValue="Active"
                    placeholder="Select or type Status"
                    className={cn(
                      'w-full px-3 py-2 rounded-xl text-sm outline-none border transition-colors',
                      isDark
                        ? 'bg-zinc-800 border-zinc-700 text-zinc-100 focus:border-brand-500'
                        : 'bg-white border-zinc-200 text-zinc-900 focus:border-brand-500'
                    )}
                  />
                  <datalist id="add-status-list">
                    {['Active', 'Inactive', 'Discontinued'].map((s) => (
                      <option key={s} value={s} />
                    ))}
                  </datalist>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-zinc-400 mb-1">Color</label>
                  <input
                    type="text"
                    name="Color"
                    placeholder="e.g. White"
                    className={cn(
                      'w-full px-3 py-2 rounded-xl text-sm outline-none border transition-colors',
                      isDark
                        ? 'bg-zinc-800 border-zinc-700 text-zinc-100 focus:border-brand-500'
                        : 'bg-white border-zinc-200 text-zinc-900 focus:border-brand-500'
                    )}
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-zinc-400 mb-1">Size</label>
                  <input
                    type="text"
                    name="Size"
                    placeholder="e.g. L"
                    className={cn(
                      'w-full px-3 py-2 rounded-xl text-sm outline-none border transition-colors',
                      isDark
                        ? 'bg-zinc-800 border-zinc-700 text-zinc-100 focus:border-brand-500'
                        : 'bg-white border-zinc-200 text-zinc-900 focus:border-brand-500'
                    )}
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-zinc-400 mb-1">Gender</label>
                  <input
                    type="text"
                    name="Gender"
                    list="add-gender-list"
                    placeholder="Select or type Gender"
                    className={cn(
                      'w-full px-3 py-2 rounded-xl text-sm outline-none border transition-colors',
                      isDark
                        ? 'bg-zinc-800 border-zinc-700 text-zinc-100 focus:border-brand-500'
                        : 'bg-white border-zinc-200 text-zinc-900 focus:border-brand-500'
                    )}
                  />
                  <datalist id="add-gender-list">
                    {['Men', 'Women', 'Unisex', 'Kids'].map((g) => (
                      <option key={g} value={g} />
                    ))}
                  </datalist>
                </div>
              </div>

              <div className="flex gap-3 justify-end pt-4">
                <button
                  type="button"
                  onClick={() => setIsAddModalOpen(false)}
                  className={cn(
                    'px-4 py-2 rounded-xl text-sm font-medium transition-colors border',
                    isDark
                      ? 'border-zinc-800 text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200'
                      : 'border-zinc-200 text-zinc-500 hover:bg-zinc-50'
                  )}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl text-sm font-medium text-white gradient-brand hover:opacity-90 transition-opacity"
                >
                  Save Product
                </button>
              </div>
            </form>
          </motion.div>
        </motion.div>
      )}

      {/* Edit Product Modal */}
      {editingProduct && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 overflow-y-auto"
          onClick={() => setEditingProduct(null)}
        >
          <motion.div
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            onClick={(e) => e.stopPropagation()}
            className={cn(
              'w-full max-w-xl rounded-2xl p-6 border my-8',
              isDark ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-zinc-200'
            )}
          >
            <div className="flex items-center justify-between mb-4">
              <h2 className={cn('text-lg font-bold', isDark ? 'text-zinc-100' : 'text-zinc-900')}>Edit Product</h2>
              <button onClick={() => setEditingProduct(null)} className="text-zinc-500 hover:text-zinc-300">
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleEditSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-zinc-400 mb-1">Product ID (Read-only)</label>
                  <input
                    type="text"
                    name="ProductID"
                    readOnly
                    defaultValue={editingProduct.ProductID}
                    className={cn(
                      'w-full px-3 py-2 rounded-xl text-sm outline-none border opacity-60 bg-zinc-800 border-zinc-700 text-zinc-400'
                    )}
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-zinc-400 mb-1">SKU</label>
                  <input
                    type="text"
                    name="SKU"
                    required
                    defaultValue={editingProduct.SKU}
                    placeholder="e.g. RAM-VESH-0501"
                    className={cn(
                      'w-full px-3 py-2 rounded-xl text-sm outline-none border transition-colors',
                      isDark
                        ? 'bg-zinc-800 border-zinc-700 text-zinc-100 focus:border-brand-500'
                        : 'bg-white border-zinc-200 text-zinc-900 focus:border-brand-500'
                    )}
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-zinc-400 mb-1">Product Name</label>
                <input
                  type="text"
                  name="ProductName"
                  required
                  defaultValue={editingProduct.ProductName}
                  placeholder="e.g. Ramraj Cotton White Veshti"
                  className={cn(
                    'w-full px-3 py-2 rounded-xl text-sm outline-none border transition-colors',
                    isDark
                      ? 'bg-zinc-800 border-zinc-700 text-zinc-100 focus:border-brand-500'
                      : 'bg-white border-zinc-200 text-zinc-900 focus:border-brand-500'
                  )}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-zinc-400 mb-1">Category</label>
                  <input
                    type="text"
                    name="Category"
                    required
                    defaultValue={editingProduct.Category}
                    list="edit-category-list"
                    placeholder="Select or type Category"
                    className={cn(
                      'w-full px-3 py-2 rounded-xl text-sm outline-none border transition-colors',
                      isDark
                        ? 'bg-zinc-800 border-zinc-700 text-zinc-100 focus:border-brand-500'
                        : 'bg-white border-zinc-200 text-zinc-900 focus:border-brand-500'
                    )}
                  />
                  <datalist id="edit-category-list">
                    {['Men', 'Women', 'Kids', 'Accessories', 'Home & Lifestyle'].map((c) => (
                      <option key={c} value={c} />
                    ))}
                  </datalist>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-zinc-400 mb-1">Sub-Category</label>
                  <input
                    type="text"
                    name="SubCategory"
                    required
                    defaultValue={editingProduct.SubCategory}
                    placeholder="e.g. Veshti"
                    className={cn(
                      'w-full px-3 py-2 rounded-xl text-sm outline-none border transition-colors',
                      isDark
                        ? 'bg-zinc-800 border-zinc-700 text-zinc-100 focus:border-brand-500'
                        : 'bg-white border-zinc-200 text-zinc-900 focus:border-brand-500'
                    )}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-zinc-400 mb-1">Brand</label>
                  <input
                    type="text"
                    name="Brand"
                    required
                    defaultValue={editingProduct.Brand}
                    list="edit-brand-list"
                    placeholder="Select or type Brand"
                    className={cn(
                      'w-full px-3 py-2 rounded-xl text-sm outline-none border transition-colors',
                      isDark
                        ? 'bg-zinc-800 border-zinc-700 text-zinc-100 focus:border-brand-500'
                        : 'bg-white border-zinc-200 text-zinc-900 focus:border-brand-500'
                    )}
                  />
                  <datalist id="edit-brand-list">
                    {['Ramraj Cotton', 'Uathayam', 'Biba', 'Fabindia', 'Prisma', 'Westside', 'Guess', 'Netplay', 'Kanchipuram Handloom', 'Raymond', 'Nandu Lungi'].map((brand) => (
                      <option key={brand} value={brand} />
                    ))}
                  </datalist>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-zinc-400 mb-1">Fabric</label>
                  <input
                    type="text"
                    name="Fabric"
                    required
                    defaultValue={editingProduct.Fabric || ''}
                    list="edit-fabric-list"
                    placeholder="Select or type Fabric"
                    className={cn(
                      'w-full px-3 py-2 rounded-xl text-sm outline-none border transition-colors',
                      isDark
                        ? 'bg-zinc-800 border-zinc-700 text-zinc-100 focus:border-brand-500'
                        : 'bg-white border-zinc-200 text-zinc-900 focus:border-brand-500'
                    )}
                  />
                  <datalist id="edit-fabric-list">
                    {['Cotton', 'Silk', 'Handloom', 'Polyester', 'Polyester Blend', 'Linen', 'Leather'].map((fabric) => (
                      <option key={fabric} value={fabric} />
                    ))}
                  </datalist>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-zinc-400 mb-1">Price (₹)</label>
                  <input
                    type="number"
                    name="Price"
                    step="0.01"
                    required
                    defaultValue={editingProduct.Price}
                    placeholder="0.00"
                    className={cn(
                      'w-full px-3 py-2 rounded-xl text-sm outline-none border transition-colors',
                      isDark
                        ? 'bg-zinc-800 border-zinc-700 text-zinc-100 focus:border-brand-500'
                        : 'bg-white border-zinc-200 text-zinc-900 focus:border-brand-500'
                    )}
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-zinc-400 mb-1">Cost Price (₹)</label>
                  <input
                    type="number"
                    name="CostPrice"
                    step="0.01"
                    required
                    defaultValue={editingProduct.CostPrice}
                    placeholder="0.00"
                    className={cn(
                      'w-full px-3 py-2 rounded-xl text-sm outline-none border transition-colors',
                      isDark
                        ? 'bg-zinc-800 border-zinc-700 text-zinc-100 focus:border-brand-500'
                        : 'bg-white border-zinc-200 text-zinc-900 focus:border-brand-500'
                    )}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-zinc-400 mb-1">Supplier</label>
                  <select
                    name="SupplierID"
                    required
                    defaultValue={editingProduct.SupplierID}
                    className={cn(
                      'w-full px-3 py-2 rounded-xl text-sm outline-none border transition-colors cursor-pointer',
                      isDark
                        ? 'bg-zinc-800 border-zinc-700 text-zinc-100 focus:border-brand-500'
                        : 'bg-white border-zinc-200 text-zinc-900 focus:border-brand-500'
                    )}
                  >
                    <option value="SUP001">Ramraj Cotton</option>
                    <option value="SUP002">Raymond</option>
                    <option value="SUP003">Biba</option>
                    <option value="SUP004">Fabindia</option>
                    <option value="SUP005">Westside</option>
                    <option value="SUP006">Uathayam</option>
                    <option value="SUP007">Prisma</option>
                    <option value="SUP008">Guess</option>
                    <option value="SUP009">Nandu Lungi</option>
                    <option value="SUP010">Peter England</option>
                    <option value="SUP011">Louis Philippe</option>
                    <option value="SUP012">Allen Solly</option>
                    <option value="SUP013">Van Heusen</option>
                    <option value="SUP014">Levi's</option>
                    <option value="SUP015">Pepe Jeans</option>
                    <option value="SUP016">US Polo</option>
                    <option value="SUP017">Arrow</option>
                    <option value="SUP018">Nike</option>
                    <option value="SUP019">Adidas</option>
                    <option value="SUP020">Puma</option>
                    <option value="SUP021">Campus</option>
                    <option value="SUP022">Jockey</option>
                    <option value="SUP023">Lux</option>
                    <option value="SUP024">VIP</option>
                    <option value="SUP025">Wildcraft</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-zinc-400 mb-1">Status</label>
                  <input
                    type="text"
                    name="ProductStatus"
                    list="edit-status-list"
                    defaultValue={editingProduct.ProductStatus || 'Active'}
                    placeholder="Select or type Status"
                    className={cn(
                      'w-full px-3 py-2 rounded-xl text-sm outline-none border transition-colors',
                      isDark
                        ? 'bg-zinc-800 border-zinc-700 text-zinc-100 focus:border-brand-500'
                        : 'bg-white border-zinc-200 text-zinc-900 focus:border-brand-500'
                    )}
                  />
                  <datalist id="edit-status-list">
                    {['Active', 'Inactive', 'Discontinued'].map((s) => (
                      <option key={s} value={s} />
                    ))}
                  </datalist>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-zinc-400 mb-1">Color</label>
                  <input
                    type="text"
                    name="Color"
                    defaultValue={editingProduct.Color || ''}
                    placeholder="e.g. White"
                    className={cn(
                      'w-full px-3 py-2 rounded-xl text-sm outline-none border transition-colors',
                      isDark
                        ? 'bg-zinc-800 border-zinc-700 text-zinc-100 focus:border-brand-500'
                        : 'bg-white border-zinc-200 text-zinc-900 focus:border-brand-500'
                    )}
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-zinc-400 mb-1">Size</label>
                  <input
                    type="text"
                    name="Size"
                    defaultValue={editingProduct.Size || ''}
                    placeholder="e.g. L"
                    className={cn(
                      'w-full px-3 py-2 rounded-xl text-sm outline-none border transition-colors',
                      isDark
                        ? 'bg-zinc-800 border-zinc-700 text-zinc-100 focus:border-brand-500'
                        : 'bg-white border-zinc-200 text-zinc-900 focus:border-brand-500'
                    )}
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-zinc-400 mb-1">Gender</label>
                  <input
                    type="text"
                    name="Gender"
                    defaultValue={editingProduct.Gender || ''}
                    list="edit-gender-list"
                    placeholder="Select or type Gender"
                    className={cn(
                      'w-full px-3 py-2 rounded-xl text-sm outline-none border transition-colors',
                      isDark
                        ? 'bg-zinc-800 border-zinc-700 text-zinc-100 focus:border-brand-500'
                        : 'bg-white border-zinc-200 text-zinc-900 focus:border-brand-500'
                    )}
                  />
                  <datalist id="edit-gender-list">
                    {['Men', 'Women', 'Unisex', 'Kids'].map((g) => (
                      <option key={g} value={g} />
                    ))}
                  </datalist>
                </div>
              </div>

              <div className="flex gap-3 justify-end pt-4">
                <button
                  type="button"
                  onClick={() => setEditingProduct(null)}
                  className={cn(
                    'px-4 py-2 rounded-xl text-sm font-medium transition-colors border',
                    isDark
                      ? 'border-zinc-800 text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200'
                      : 'border-zinc-200 text-zinc-500 hover:bg-zinc-50'
                  )}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl text-sm font-medium text-white gradient-brand hover:opacity-90 transition-opacity"
                >
                  Save Changes
                </button>
              </div>
            </form>
          </motion.div>
        </motion.div>
      )}
    </motion.div>
  );
}
