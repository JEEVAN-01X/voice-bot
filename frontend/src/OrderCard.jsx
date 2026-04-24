const LANG_LABELS = {'en-IN':'EN','hi-IN':'HI','kn-IN':'KN','mr-IN':'MR'};
const LANG_COLORS = {
  'en-IN':'bg-blue-100 text-blue-800',
  'hi-IN':'bg-orange-100 text-orange-800',
  'kn-IN':'bg-green-100 text-green-800',
  'mr-IN':'bg-purple-100 text-purple-800'
};

export default function OrderCard({ order }) {
  return (
    <div className='bg-white rounded-xl border border-gray-200 p-4 shadow-sm'>
      <div className='flex justify-between items-start'>
        <div>
          <p className='font-semibold text-gray-900'>{order.customer_phone}</p>
          <p className='text-sm text-gray-500 mt-1'>{order.items?.join(' · ')}</p>
          {order.address && <p className='text-xs text-gray-400 mt-1'>{order.address}</p>}
        </div>
        <span className={`text-xs font-bold px-2 py-1 rounded-full ${LANG_COLORS[order.language]}`}>
          {LANG_LABELS[order.language]}
        </span>
      </div>
      <div className='mt-3 flex justify-between items-center'>
        <span className='text-xs text-green-600 font-medium'>✅ Confirmed</span>
        <span className='text-xs text-gray-400'>
          {order.confirmed_at?.seconds
            ? new Date(order.confirmed_at.seconds*1000).toLocaleTimeString()
            : 'Just now'}
        </span>
      </div>
    </div>
  );
}
