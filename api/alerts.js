const {observe}=require('../lib/watchdog.cjs');
module.exports=(req,res)=>{const d=observe();res.setHeader('Cache-Control','no-store');res.status(200).json({site:'junkremoval.ltd',checkedAt:d.observedAt,events:[d.incident,{...d.probe,runUrl:'https://junkremoval-ltd.vercel.app/api/watchdog'}],publications:[],fourRolesApproved:false,ownerReadVerified:false});};
